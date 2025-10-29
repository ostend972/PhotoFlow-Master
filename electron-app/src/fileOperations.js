/**
 * Module de gestion des opérations sur les fichiers
 * Gère la copie, le déplacement, l'analyse et la vérification des fichiers
 */

const fs = require('fs-extra');
const path = require('path');
const crypto = require('crypto');
const { glob } = require('glob');

// Extensions d'images supportées
const IMAGE_EXTENSIONS = [
  '.jpg', '.jpeg', '.png', '.tiff', '.tif',
  '.arw', '.cr2', '.nef', '.raf', '.dng',
  '.heic', '.heif', '.webp', '.bmp'
];

class FileOperations {
  /**
   * Analyser un dossier de manière asynchrone
   * @param {string} folderPath - Chemin du dossier à analyser
   * @returns {Promise<Object>} Statistiques du dossier
   */
  static async analyzeFolderAsync(folderPath) {
    try {
      const stats = await this.getFolderStatistics(folderPath);

      return {
        exists: true,
        totalFiles: stats.totalFiles,
        totalSize: stats.totalSize,
        fileTypes: stats.fileTypes,
        imageFiles: stats.imageFiles
      };
    } catch (error) {
      console.error('Erreur lors de l\'analyse du dossier:', error);
      return {
        exists: false,
        error: error.message
      };
    }
  }

  /**
   * Obtenir les statistiques détaillées d'un dossier
   * @param {string} folderPath - Chemin du dossier
   * @returns {Promise<Object>} Statistiques complètes
   */
  static async getFolderStatistics(folderPath) {
    let totalFiles = 0;
    let totalSize = 0;
    let imageFiles = 0;
    const fileTypes = {};

    try {
      // Utiliser glob pour trouver tous les fichiers récursivement
      const pattern = path.join(folderPath, '**', '*').replace(/\\/g, '/');
      const files = await glob(pattern, { nodir: true });

      for (const file of files) {
        try {
          const stat = await fs.stat(file);

          if (stat.isFile()) {
            totalFiles++;
            totalSize += stat.size;

            const ext = path.extname(file).toLowerCase();

            // Compter par type
            fileTypes[ext] = (fileTypes[ext] || 0) + 1;

            // Compter les images
            if (IMAGE_EXTENSIONS.includes(ext)) {
              imageFiles++;
            }
          }
        } catch (fileError) {
          // Ignorer les fichiers inaccessibles
          console.warn(`Fichier ignoré: ${file}`, fileError.message);
        }
      }

      return {
        totalFiles,
        totalSize,
        imageFiles,
        fileTypes
      };
    } catch (error) {
      console.error('Erreur lors du calcul des statistiques:', error);
      throw error;
    }
  }

  /**
   * Obtenir tous les fichiers images d'un dossier
   * @param {string} folderPath - Chemin du dossier
   * @returns {Promise<Array<string>>} Liste des chemins de fichiers images
   */
  static async getImageFiles(folderPath) {
    try {
      const pattern = path.join(folderPath, '**', '*').replace(/\\/g, '/');
      const allFiles = await glob(pattern, { nodir: true });

      // Filtrer uniquement les images
      const imageFiles = allFiles.filter(file => {
        const ext = path.extname(file).toLowerCase();
        return IMAGE_EXTENSIONS.includes(ext);
      });

      return imageFiles;
    } catch (error) {
      console.error('Erreur lors de la récupération des fichiers images:', error);
      throw error;
    }
  }

  /**
   * Copier un fichier avec gestion des doublons
   * @param {string} sourcePath - Chemin source
   * @param {string} destPath - Chemin destination
   * @param {string} duplicateStrategy - Stratégie pour les doublons (rename, skip, replace)
   * @returns {Promise<string>} Chemin final du fichier
   */
  static async copyFile(sourcePath, destPath, duplicateStrategy = 'rename') {
    try {
      // Gérer les doublons
      const finalPath = await this.handleDuplicate(destPath, duplicateStrategy);

      if (!finalPath) {
        // Skip - ne pas copier
        return null;
      }

      // Assurer que le dossier de destination existe
      await fs.ensureDir(path.dirname(finalPath));

      // Copier le fichier avec préservation des métadonnées
      await fs.copy(sourcePath, finalPath, {
        preserveTimestamps: true,
        overwrite: duplicateStrategy === 'replace'
      });

      return finalPath;
    } catch (error) {
      console.error(`Erreur lors de la copie de ${sourcePath}:`, error);
      throw error;
    }
  }

  /**
   * Déplacer un fichier avec gestion des doublons
   * @param {string} sourcePath - Chemin source
   * @param {string} destPath - Chemin destination
   * @param {string} duplicateStrategy - Stratégie pour les doublons
   * @returns {Promise<string>} Chemin final du fichier
   */
  static async moveFile(sourcePath, destPath, duplicateStrategy = 'rename') {
    try {
      const finalPath = await this.handleDuplicate(destPath, duplicateStrategy);

      if (!finalPath) {
        return null;
      }

      await fs.ensureDir(path.dirname(finalPath));
      await fs.move(sourcePath, finalPath, {
        overwrite: duplicateStrategy === 'replace'
      });

      return finalPath;
    } catch (error) {
      console.error(`Erreur lors du déplacement de ${sourcePath}:`, error);
      throw error;
    }
  }

  /**
   * Créer un lien symbolique
   * @param {string} sourcePath - Chemin source
   * @param {string} destPath - Chemin destination
   * @param {string} duplicateStrategy - Stratégie pour les doublons
   * @returns {Promise<string>} Chemin final du lien
   */
  static async createSymlink(sourcePath, destPath, duplicateStrategy = 'rename') {
    try {
      const finalPath = await this.handleDuplicate(destPath, duplicateStrategy);

      if (!finalPath) {
        return null;
      }

      await fs.ensureDir(path.dirname(finalPath));

      // Créer le lien symbolique
      await fs.symlink(sourcePath, finalPath, 'file');

      return finalPath;
    } catch (error) {
      console.error(`Erreur lors de la création du lien symbolique ${sourcePath}:`, error);
      throw error;
    }
  }

  /**
   * Gérer les fichiers en double selon la stratégie
   * @param {string} filePath - Chemin du fichier
   * @param {string} strategy - Stratégie (rename, skip, replace)
   * @returns {Promise<string|null>} Nouveau chemin ou null si skip
   */
  static async handleDuplicate(filePath, strategy) {
    const exists = await fs.pathExists(filePath);

    if (!exists) {
      return filePath;
    }

    if (strategy === 'skip') {
      return null;
    }

    if (strategy === 'replace') {
      return filePath;
    }

    if (strategy === 'rename') {
      // Renommer avec un compteur
      const dir = path.dirname(filePath);
      const ext = path.extname(filePath);
      const name = path.basename(filePath, ext);

      let counter = 1;
      let newPath = path.join(dir, `${name}_${counter}${ext}`);

      while (await fs.pathExists(newPath)) {
        counter++;
        newPath = path.join(dir, `${name}_${counter}${ext}`);
      }

      return newPath;
    }

    return filePath;
  }

  /**
   * Appliquer un pattern de renommage
   * @param {string} filePath - Chemin du fichier
   * @param {string} pattern - Pattern de renommage
   * @param {Object} data - Données pour le renommage (project, date, counter)
   * @returns {string} Nouveau nom de fichier
   */
  static applyRenamePattern(filePath, pattern, data) {
    const ext = path.extname(filePath);
    const originalName = path.basename(filePath, ext);

    let newName = pattern
      .replace('{original}', originalName)
      .replace('{project}', data.project || 'Project')
      .replace('{date}', data.date || '')
      .replace('{counter:04d}', String(data.counter || 0).padStart(4, '0'))
      .replace('{ext}', ext);

    return newName + ext;
  }

  /**
   * Vérifier l'intégrité d'un fichier copié via checksum MD5
   * @param {string} sourcePath - Fichier source
   * @param {string} destPath - Fichier destination
   * @returns {Promise<boolean>} true si les checksums correspondent
   */
  static async verifyIntegrity(sourcePath, destPath) {
    try {
      const sourceHash = await this.calculateChecksum(sourcePath);
      const destHash = await this.calculateChecksum(destPath);

      return sourceHash === destHash;
    } catch (error) {
      console.error('Erreur lors de la vérification d\'intégrité:', error);
      return false;
    }
  }

  /**
   * Calculer le checksum MD5 d'un fichier
   * @param {string} filePath - Chemin du fichier
   * @returns {Promise<string>} Hash MD5 en hexadécimal
   */
  static async calculateChecksum(filePath) {
    return new Promise((resolve, reject) => {
      const hash = crypto.createHash('md5');
      const stream = fs.createReadStream(filePath);

      stream.on('data', (data) => hash.update(data));
      stream.on('end', () => resolve(hash.digest('hex')));
      stream.on('error', reject);
    });
  }

  /**
   * Formater une taille en octets en format lisible
   * @param {number} bytes - Taille en octets
   * @returns {string} Taille formatée
   */
  static formatSize(bytes) {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(2)} ${units[unitIndex]}`;
  }

  /**
   * Nettoyer un nom de fichier pour éviter les caractères interdits
   * @param {string} filename - Nom à nettoyer
   * @returns {string} Nom nettoyé
   */
  static sanitizeFilename(filename) {
    // Remplacer les caractères interdits par des underscores
    return filename.replace(/[<>:"/\\|?*\x00-\x1F]/g, '_');
  }
}

module.exports = FileOperations;
