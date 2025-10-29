/**
 * Module de création de la structure de dossiers professionnelle
 * Crée l'arborescence standard pour les projets photo professionnels
 */

const fs = require('fs-extra');
const path = require('path');

/**
 * Structure de dossiers professionnelle standard
 * Adaptée aux besoins des photographes professionnels
 */
const PROJECT_STRUCTURE = {
  '01_PRE-PRODUCTION': {
    description: 'Préparation et conception du projet',
    subfolders: ['Moodboard', 'References', 'Brief', 'Planning']
  },
  '02_RAW': {
    description: 'Fichiers RAW et photos sources originales',
    subfolders: [] // Pas de sous-dossiers, tous les RAW au même niveau
  },
  '03_SELECTS': {
    description: 'Sélection des meilleures photos',
    subfolders: ['First_Pass', 'Final_Selection']
  },
  '04_RETOUCHE': {
    description: 'Retouches et édition des photos',
    subfolders: ['PSD', 'FINALS', 'Client_Review']
  },
  '05_VIDEO': {
    description: 'Contenu vidéo du projet',
    subfolders: ['RUSH', 'EDITS', 'FINALS']
  },
  '06_ADMIN': {
    description: 'Documents administratifs',
    subfolders: ['Factures', 'Contrats', 'Correspondance', 'Releases']
  }
};

class ProjectStructure {
  /**
   * Créer la structure complète d'un projet photo
   * @param {string} projectPath - Chemin racine du projet
   * @param {Object} options - Options de personnalisation
   * @returns {Promise<Object>} Résultat de la création
   */
  static async createProjectStructure(projectPath, options = {}) {
    try {
      const createdFolders = [];
      const errors = [];

      // Créer le dossier racine du projet
      await fs.ensureDir(projectPath);
      createdFolders.push(projectPath);

      console.log(`📁 Création de la structure dans: ${projectPath}`);

      // Créer chaque dossier principal et ses sous-dossiers
      for (const [folderName, config] of Object.entries(PROJECT_STRUCTURE)) {
        try {
          const folderPath = path.join(projectPath, folderName);

          // Créer le dossier principal
          await fs.ensureDir(folderPath);
          createdFolders.push(folderPath);

          console.log(`  ✅ ${folderName} - ${config.description}`);

          // Créer les sous-dossiers
          for (const subfolder of config.subfolders) {
            const subfolderPath = path.join(folderPath, subfolder);
            await fs.ensureDir(subfolderPath);
            createdFolders.push(subfolderPath);

            console.log(`    ↳ ${subfolder}`);
          }

          // Créer un fichier README dans chaque dossier principal
          if (options.createReadme !== false) {
            await this.createReadmeFile(folderPath, folderName, config.description);
          }

        } catch (folderError) {
          const error = {
            folder: folderName,
            message: folderError.message
          };
          errors.push(error);
          console.error(`  ❌ Erreur avec ${folderName}:`, folderError.message);
        }
      }

      // Créer un fichier README racine du projet
      if (options.createReadme !== false) {
        await this.createProjectReadme(projectPath, options.projectName || path.basename(projectPath));
      }

      // Créer un fichier .gitignore si demandé
      if (options.createGitignore) {
        await this.createGitignore(projectPath);
      }

      console.log(`✨ Structure créée avec succès: ${createdFolders.length} dossiers`);

      return {
        success: true,
        projectPath,
        createdFolders: createdFolders.length,
        errors: errors.length > 0 ? errors : null
      };

    } catch (error) {
      console.error('Erreur fatale lors de la création de la structure:', error);
      throw error;
    }
  }

  /**
   * Créer un fichier README dans un dossier
   * @param {string} folderPath - Chemin du dossier
   * @param {string} folderName - Nom du dossier
   * @param {string} description - Description du dossier
   */
  static async createReadmeFile(folderPath, folderName, description) {
    try {
      const readmePath = path.join(folderPath, 'README.md');

      // Ne pas écraser un README existant
      if (await fs.pathExists(readmePath)) {
        return;
      }

      const content = `# ${folderName}

${description}

## Contenu

Ce dossier contient les fichiers liés à: ${description.toLowerCase()}

## Instructions

Organisez vos fichiers dans ce dossier selon vos besoins.

---
*Créé automatiquement par PhotoFlow Master*
`;

      await fs.writeFile(readmePath, content, 'utf8');
    } catch (error) {
      console.warn(`Impossible de créer le README dans ${folderPath}:`, error.message);
    }
  }

  /**
   * Créer le README principal du projet
   * @param {string} projectPath - Chemin du projet
   * @param {string} projectName - Nom du projet
   */
  static async createProjectReadme(projectPath, projectName) {
    try {
      const readmePath = path.join(projectPath, 'README.md');

      if (await fs.pathExists(readmePath)) {
        return;
      }

      const content = `# ${projectName}

## Structure du Projet

Ce projet utilise une structure standard professionnelle pour l'organisation des photos:

### 📁 01_PRE-PRODUCTION
Préparation et planification du projet
- Moodboard: Inspirations visuelles
- References: Images de référence
- Brief: Documents de briefing client
- Planning: Planification des shootings

### 📸 02_RAW
Fichiers RAW et photos sources originales
- Tous les fichiers RAW non traités

### ✨ 03_SELECTS
Sélection des meilleures photos
- First_Pass: Première sélection
- Final_Selection: Sélection finale

### 🎨 04_RETOUCHE
Retouches et édition des photos
- PSD: Fichiers Photoshop en cours
- FINALS: Images finales livrables
- Client_Review: Fichiers pour revue client

### 🎬 05_VIDEO
Contenu vidéo du projet
- RUSH: Rushs vidéo bruts
- EDITS: Montages en cours
- FINALS: Vidéos finales

### 📄 06_ADMIN
Documents administratifs et légaux
- Factures: Facturation client
- Contrats: Contrats et accords
- Correspondance: Emails et communications
- Releases: Autorisations de droits d'image

## Workflow Recommandé

1. **Préparation** (01_PRE-PRODUCTION): Planifier le shooting
2. **Import** (02_RAW): Importer tous les RAW
3. **Sélection** (03_SELECTS): Faire la sélection des meilleures images
4. **Édition** (04_RETOUCHE): Retoucher les images sélectionnées
5. **Livraison** (04_RETOUCHE/FINALS): Livrer au client
6. **Administration** (06_ADMIN): Archiver les documents

---

**Projet créé le:** ${new Date().toLocaleDateString('fr-FR')}
**Outil:** PhotoFlow Master
**Version:** 1.0.0
`;

      await fs.writeFile(readmePath, content, 'utf8');
    } catch (error) {
      console.warn('Impossible de créer le README principal:', error.message);
    }
  }

  /**
   * Créer un fichier .gitignore pour le projet
   * @param {string} projectPath - Chemin du projet
   */
  static async createGitignore(projectPath) {
    try {
      const gitignorePath = path.join(projectPath, '.gitignore');

      const content = `# PhotoFlow Master - .gitignore

# Fichiers système
.DS_Store
Thumbs.db
desktop.ini

# Fichiers temporaires
*.tmp
*.temp
~*

# Fichiers de sauvegarde
*.bak
*.backup

# Fichiers d'application
*.lock
*.log

# Gros fichiers (décommenter si nécessaire)
# 02_RAW/**/*
# 04_RETOUCHE/PSD/**/*
# 05_VIDEO/RUSH/**/*
`;

      await fs.writeFile(gitignorePath, content, 'utf8');
    } catch (error) {
      console.warn('Impossible de créer le .gitignore:', error.message);
    }
  }

  /**
   * Vérifier si une structure de projet existe déjà
   * @param {string} projectPath - Chemin à vérifier
   * @returns {Promise<boolean>} true si la structure existe
   */
  static async projectExists(projectPath) {
    try {
      if (!await fs.pathExists(projectPath)) {
        return false;
      }

      // Vérifier si au moins les dossiers principaux existent
      const mainFolders = Object.keys(PROJECT_STRUCTURE);
      let existingCount = 0;

      for (const folder of mainFolders) {
        const folderPath = path.join(projectPath, folder);
        if (await fs.pathExists(folderPath)) {
          existingCount++;
        }
      }

      // Si plus de la moitié des dossiers existent, considérer que le projet existe
      return existingCount >= mainFolders.length / 2;
    } catch (error) {
      return false;
    }
  }

  /**
   * Obtenir des informations sur un projet existant
   * @param {string} projectPath - Chemin du projet
   * @returns {Promise<Object>} Informations sur le projet
   */
  static async getProjectInfo(projectPath) {
    try {
      const info = {
        exists: await fs.pathExists(projectPath),
        folders: {},
        totalSize: 0,
        fileCount: 0
      };

      if (!info.exists) {
        return info;
      }

      for (const folder of Object.keys(PROJECT_STRUCTURE)) {
        const folderPath = path.join(projectPath, folder);
        const exists = await fs.pathExists(folderPath);

        info.folders[folder] = {
          exists,
          path: folderPath
        };

        if (exists) {
          try {
            // Compter les fichiers et la taille (simple, pas récursif)
            const files = await fs.readdir(folderPath);
            info.folders[folder].fileCount = files.length;
          } catch (e) {
            info.folders[folder].fileCount = 0;
          }
        }
      }

      return info;
    } catch (error) {
      console.error('Erreur lors de la récupération des infos du projet:', error);
      return { exists: false, error: error.message };
    }
  }

  /**
   * Obtenir la structure en tant qu'objet (pour affichage)
   * @returns {Object} Structure des dossiers
   */
  static getStructureDefinition() {
    return PROJECT_STRUCTURE;
  }
}

module.exports = ProjectStructure;
