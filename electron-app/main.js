const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs-extra');
const { format } = require('date-fns');

// Import des modules métier
const FileOperations = require('./src/fileOperations');
const ExifReader = require('./src/exifReader');
const ProjectStructure = require('./src/projectStructure');

// Variable pour la fenêtre principale
let mainWindow;

// Création de la fenêtre principale
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    backgroundColor: '#1a1a2e',
    icon: path.join(__dirname, 'assets', 'icon.png'),
    webPreferences: {
      nodeIntegration: false, // Sécurité : pas d'intégration Node dans le renderer
      contextIsolation: true, // Isolation du contexte pour la sécurité
      preload: path.join(__dirname, 'preload.js') // Script preload pour le pont IPC
    },
    show: false, // Ne pas afficher tant que prêt
    frame: true,
    titleBarStyle: 'default'
  });

  // Charger l'interface HTML
  mainWindow.loadFile('renderer/index.html');

  // Afficher la fenêtre quand elle est prête
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Outils de développement en mode dev
  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();
  }

  // Gestion de la fermeture
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Initialisation de l'application
app.whenReady().then(() => {
  createWindow();

  // Sur macOS, recréer la fenêtre si l'icône du dock est cliquée
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Quitter quand toutes les fenêtres sont fermées (sauf sur macOS)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// ===== GESTIONNAIRES IPC =====

/**
 * Sélectionner un dossier source
 */
ipcMain.handle('select-folder', async (event) => {
  try {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openDirectory'],
      title: 'Sélectionnez un dossier source'
    });

    if (result.canceled || result.filePaths.length === 0) {
      return { success: false, canceled: true };
    }

    const folderPath = result.filePaths[0];

    // Analyser le dossier pour obtenir des informations
    const analysis = await FileOperations.analyzeFolderAsync(folderPath);

    return {
      success: true,
      path: folderPath,
      name: path.basename(folderPath),
      ...analysis
    };
  } catch (error) {
    console.error('Erreur lors de la sélection du dossier:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

/**
 * Sélectionner un dossier de destination
 */
ipcMain.handle('select-destination', async (event) => {
  try {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openDirectory'],
      title: 'Sélectionnez le dossier de destination'
    });

    if (result.canceled || result.filePaths.length === 0) {
      return { success: false, canceled: true };
    }

    const folderPath = result.filePaths[0];

    // Vérifier l'espace disque disponible
    const stats = await fs.statfs(folderPath);
    const freeSpace = stats.bavail * stats.bsize;

    return {
      success: true,
      path: folderPath,
      freeSpace: freeSpace
    };
  } catch (error) {
    console.error('Erreur lors de la sélection de la destination:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

/**
 * Détecter la date de shooting à partir des EXIF
 */
ipcMain.handle('detect-date', async (event, folderPath) => {
  try {
    const exifReader = new ExifReader();
    const date = await exifReader.findEarliestDate(folderPath);

    if (date) {
      return {
        success: true,
        date: date.toISOString(),
        formatted: format(date, 'dd-MM-yyyy')
      };
    } else {
      return {
        success: false,
        message: 'Aucune date EXIF trouvée dans les photos'
      };
    }
  } catch (error) {
    console.error('Erreur lors de la détection de la date:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

/**
 * Obtenir des statistiques détaillées sur les sources
 */
ipcMain.handle('get-statistics', async (event, sources) => {
  try {
    let totalFiles = 0;
    let totalSize = 0;
    const fileTypeStats = {};
    const filesBySource = [];

    for (const source of sources) {
      const stats = await FileOperations.getFolderStatistics(source.path);

      totalFiles += stats.totalFiles;
      totalSize += stats.totalSize;

      // Fusionner les statistiques par type
      for (const [ext, count] of Object.entries(stats.fileTypes)) {
        fileTypeStats[ext] = (fileTypeStats[ext] || 0) + count;
      }

      filesBySource.push({
        path: source.path,
        name: source.name,
        files: stats.totalFiles,
        size: stats.totalSize
      });
    }

    return {
      success: true,
      totalFiles,
      totalSize,
      fileTypeStats,
      filesBySource
    };
  } catch (error) {
    console.error('Erreur lors du calcul des statistiques:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

/**
 * Organiser les projets photo
 * C'est la fonction principale qui effectue tout le travail
 */
ipcMain.handle('organize-projects', async (event, options) => {
  const {
    sources,
    destination,
    copyMode,
    duplicateStrategy,
    verifyIntegrity,
    renamePattern
  } = options;

  const logFile = path.join(app.getPath('userData'), 'logs', `organization-${Date.now()}.log`);
  await fs.ensureDir(path.dirname(logFile));

  // Fonction pour logger et envoyer au renderer
  const log = async (message, level = 'info') => {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}\n`;
    await fs.appendFile(logFile, logMessage);
    mainWindow.webContents.send('log-message', { message, level, timestamp });
  };

  try {
    await log('🚀 Début de l\'organisation des projets');

    let totalProcessed = 0;
    let totalErrors = 0;
    const results = [];

    for (let i = 0; i < sources.length; i++) {
      const source = sources[i];

      // Envoyer la progression globale
      mainWindow.webContents.send('progress-update', {
        type: 'global',
        current: i,
        total: sources.length,
        currentProject: source.name
      });

      await log(`📂 Traitement du projet: ${source.name}`);

      try {
        // Créer le nom du dossier projet
        const projectDate = source.date ? source.date : format(new Date(), 'yyyy-MM-dd');
        const year = projectDate.split('-')[0];
        const projectFolderName = `${projectDate}_${source.name}`;

        // Chemin complet du projet
        const projectPath = path.join(destination, 'PROJETS_PHOTO', year, projectFolderName);

        // Créer la structure du projet
        await log(`📁 Création de la structure pour: ${projectFolderName}`);
        await ProjectStructure.createProjectStructure(projectPath);
        await log(`✅ Structure créée: ${projectPath}`);

        // Obtenir tous les fichiers à traiter
        const files = await FileOperations.getImageFiles(source.path);
        await log(`📊 ${files.length} fichiers trouvés dans ${source.name}`);

        // Traiter les fichiers
        let processed = 0;
        let errors = 0;

        for (let j = 0; j < files.length; j++) {
          const file = files[j];

          // Progression du fichier
          if (j % 10 === 0 || j === files.length - 1) {
            mainWindow.webContents.send('progress-update', {
              type: 'file',
              current: j + 1,
              total: files.length,
              filename: path.basename(file),
              project: source.name
            });
          }

          try {
            // Destination dans le dossier RAW
            const rawFolder = path.join(projectPath, '02_RAW');
            let filename = path.basename(file);

            // Appliquer le pattern de renommage si nécessaire
            if (renamePattern && renamePattern !== '{original}') {
              filename = FileOperations.applyRenamePattern(
                file,
                renamePattern,
                {
                  project: source.name,
                  date: projectDate,
                  counter: j + 1
                }
              );
            }

            const destPath = path.join(rawFolder, filename);

            // Copier ou déplacer le fichier
            if (copyMode === 'move') {
              await FileOperations.moveFile(file, destPath, duplicateStrategy);
            } else if (copyMode === 'copy') {
              await FileOperations.copyFile(file, destPath, duplicateStrategy);
            } else if (copyMode === 'symlink') {
              await FileOperations.createSymlink(file, destPath, duplicateStrategy);
            }

            // Vérification d'intégrité si demandée
            if (verifyIntegrity && copyMode !== 'symlink') {
              const isValid = await FileOperations.verifyIntegrity(file, destPath);
              if (!isValid) {
                throw new Error('Échec de la vérification d\'intégrité');
              }
            }

            processed++;
          } catch (fileError) {
            errors++;
            await log(`❌ Erreur avec ${path.basename(file)}: ${fileError.message}`, 'error');
          }
        }

        totalProcessed += processed;
        totalErrors += errors;

        results.push({
          source: source.name,
          processed,
          errors,
          projectPath
        });

        await log(`✅ Projet terminé: ${source.name} - ${processed}/${files.length} fichiers traités`);

      } catch (projectError) {
        await log(`❌ Erreur critique pour ${source.name}: ${projectError.message}`, 'error');
        results.push({
          source: source.name,
          processed: 0,
          errors: 1,
          error: projectError.message
        });
        totalErrors++;
      }
    }

    await log(`✨ Organisation terminée! ${totalProcessed} fichiers traités, ${totalErrors} erreurs`);

    return {
      success: true,
      totalProcessed,
      totalErrors,
      results,
      logFile
    };

  } catch (error) {
    await log(`💥 Erreur fatale: ${error.message}`, 'error');
    return {
      success: false,
      error: error.message,
      logFile
    };
  }
});

/**
 * Ouvrir un dossier dans l'explorateur Windows
 */
ipcMain.handle('open-folder', async (event, folderPath) => {
  try {
    const { shell } = require('electron');
    await shell.openPath(folderPath);
    return { success: true };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
});

/**
 * Obtenir les préférences utilisateur sauvegardées
 */
ipcMain.handle('get-preferences', async (event) => {
  try {
    const prefsPath = path.join(app.getPath('userData'), 'preferences.json');

    if (await fs.pathExists(prefsPath)) {
      const prefs = await fs.readJson(prefsPath);
      return { success: true, preferences: prefs };
    } else {
      return { success: true, preferences: {} };
    }
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
});

/**
 * Sauvegarder les préférences utilisateur
 */
ipcMain.handle('save-preferences', async (event, preferences) => {
  try {
    const prefsPath = path.join(app.getPath('userData'), 'preferences.json');
    await fs.ensureDir(path.dirname(prefsPath));
    await fs.writeJson(prefsPath, preferences, { spaces: 2 });
    return { success: true };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
});

/**
 * Annuler l'opération en cours
 * Note: Pour une annulation propre, il faudrait un système de gestion d'état
 * plus complexe. Ceci est une version simplifiée.
 */
ipcMain.handle('cancel-operation', async (event) => {
  // TODO: Implémenter un système d'annulation propre
  // Pour l'instant, on retourne simplement un succès
  return { success: true };
});

// Gestion des erreurs non capturées
process.on('uncaughtException', (error) => {
  console.error('Erreur non capturée:', error);
  if (mainWindow) {
    mainWindow.webContents.send('error', {
      message: 'Une erreur inattendue s\'est produite',
      details: error.message
    });
  }
});
