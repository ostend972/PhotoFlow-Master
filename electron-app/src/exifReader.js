/**
 * Module de lecture des métadonnées EXIF des photos
 * Utilise exiftool-vendored pour extraire les données EXIF de manière fiable
 */

const { exiftool } = require('exiftool-vendored');
const path = require('path');
const fs = require('fs-extra');

// Extensions supportées pour la lecture EXIF
const EXIF_SUPPORTED_EXTENSIONS = [
  '.jpg', '.jpeg', '.tiff', '.tif',
  '.arw', '.cr2', '.nef', '.raf', '.dng',
  '.heic', '.heif'
];

class ExifReader {
  constructor() {
    this.exiftoolInstance = exiftool;
  }

  /**
   * Extraire la date de prise de vue d'une image
   * @param {string} imagePath - Chemin de l'image
   * @returns {Promise<Date|null>} Date de prise de vue ou null
   */
  async extractDateTaken(imagePath) {
    try {
      // Vérifier que le fichier existe
      if (!await fs.pathExists(imagePath)) {
        return null;
      }

      // Vérifier que l'extension est supportée
      const ext = path.extname(imagePath).toLowerCase();
      if (!EXIF_SUPPORTED_EXTENSIONS.includes(ext)) {
        return null;
      }

      // Lire les métadonnées EXIF
      const metadata = await this.exiftoolInstance.read(imagePath);

      // Essayer différents champs de date (par ordre de priorité)
      const dateFields = [
        metadata.DateTimeOriginal,
        metadata.CreateDate,
        metadata.DateTimeDigitized,
        metadata.ModifyDate
      ];

      for (const dateField of dateFields) {
        if (dateField) {
          // Convertir en objet Date JavaScript
          const date = this.parseExifDate(dateField);
          if (date && !isNaN(date.getTime())) {
            return date;
          }
        }
      }

      return null;
    } catch (error) {
      console.error(`Erreur lors de la lecture EXIF de ${imagePath}:`, error.message);
      return null;
    }
  }

  /**
   * Trouver la date la plus ancienne dans un dossier d'images
   * @param {string} folderPath - Chemin du dossier
   * @returns {Promise<Date|null>} Date la plus ancienne trouvée
   */
  async findEarliestDate(folderPath) {
    try {
      // Récupérer tous les fichiers du dossier récursivement
      const files = await this.getAllFiles(folderPath);

      // Filtrer les fichiers supportés pour EXIF
      const imageFiles = files.filter(file => {
        const ext = path.extname(file).toLowerCase();
        return EXIF_SUPPORTED_EXTENSIONS.includes(ext);
      });

      if (imageFiles.length === 0) {
        console.log('Aucun fichier image trouvé pour l\'extraction EXIF');
        return null;
      }

      let earliestDate = null;

      // Limiter à 50 fichiers pour ne pas trop ralentir
      const filesToCheck = imageFiles.slice(0, 50);

      console.log(`Analyse EXIF de ${filesToCheck.length} fichiers sur ${imageFiles.length}...`);

      for (const file of filesToCheck) {
        try {
          const date = await this.extractDateTaken(file);

          if (date) {
            if (!earliestDate || date < earliestDate) {
              earliestDate = date;
              console.log(`Date trouvée: ${date.toISOString()} dans ${path.basename(file)}`);
            }
          }
        } catch (fileError) {
          // Ignorer les erreurs individuelles
          console.warn(`Impossible de lire ${file}:`, fileError.message);
        }
      }

      return earliestDate;
    } catch (error) {
      console.error('Erreur lors de la recherche de la date:', error);
      return null;
    }
  }

  /**
   * Extraire toutes les métadonnées EXIF d'une image
   * @param {string} imagePath - Chemin de l'image
   * @returns {Promise<Object|null>} Métadonnées complètes ou null
   */
  async extractAllMetadata(imagePath) {
    try {
      if (!await fs.pathExists(imagePath)) {
        return null;
      }

      const metadata = await this.exiftoolInstance.read(imagePath);

      return {
        camera: {
          make: metadata.Make || null,
          model: metadata.Model || null,
          lens: metadata.LensModel || null
        },
        settings: {
          iso: metadata.ISO || null,
          focalLength: metadata.FocalLength || null,
          aperture: metadata.FNumber || metadata.Aperture || null,
          shutterSpeed: metadata.ShutterSpeed || metadata.ExposureTime || null,
          exposureMode: metadata.ExposureMode || null,
          whiteBalance: metadata.WhiteBalance || null
        },
        date: {
          original: metadata.DateTimeOriginal || null,
          created: metadata.CreateDate || null,
          modified: metadata.ModifyDate || null
        },
        image: {
          width: metadata.ImageWidth || null,
          height: metadata.ImageHeight || null,
          orientation: metadata.Orientation || null,
          colorSpace: metadata.ColorSpace || null
        },
        gps: {
          latitude: metadata.GPSLatitude || null,
          longitude: metadata.GPSLongitude || null,
          altitude: metadata.GPSAltitude || null
        },
        copyright: {
          artist: metadata.Artist || null,
          copyright: metadata.Copyright || null
        }
      };
    } catch (error) {
      console.error(`Erreur lors de l'extraction des métadonnées de ${imagePath}:`, error);
      return null;
    }
  }

  /**
   * Parser une date EXIF en objet Date JavaScript
   * @param {string|Date} exifDate - Date au format EXIF ou objet Date
   * @returns {Date|null} Objet Date ou null
   */
  parseExifDate(exifDate) {
    try {
      if (exifDate instanceof Date) {
        return exifDate;
      }

      if (typeof exifDate === 'string') {
        // Format EXIF typique: "2025:10:29 14:30:45"
        const cleanDate = exifDate.replace(/^(\d{4}):(\d{2}):(\d{2})/, '$1-$2-$3');
        const date = new Date(cleanDate);

        if (!isNaN(date.getTime())) {
          return date;
        }
      }

      return null;
    } catch (error) {
      return null;
    }
  }

  /**
   * Récupérer tous les fichiers d'un dossier récursivement
   * @param {string} dir - Chemin du dossier
   * @param {Array<string>} fileList - Liste accumulée (usage interne)
   * @returns {Promise<Array<string>>} Liste des chemins de fichiers
   */
  async getAllFiles(dir, fileList = []) {
    try {
      const files = await fs.readdir(dir);

      for (const file of files) {
        const filePath = path.join(dir, file);
        const stat = await fs.stat(filePath);

        if (stat.isDirectory()) {
          await this.getAllFiles(filePath, fileList);
        } else {
          fileList.push(filePath);
        }
      }

      return fileList;
    } catch (error) {
      console.error(`Erreur lors de la lecture du dossier ${dir}:`, error);
      return fileList;
    }
  }

  /**
   * Vérifier si un fichier contient des données EXIF
   * @param {string} imagePath - Chemin de l'image
   * @returns {Promise<boolean>} true si des données EXIF existent
   */
  async hasExifData(imagePath) {
    try {
      const metadata = await this.exiftoolInstance.read(imagePath);
      return metadata && Object.keys(metadata).length > 0;
    } catch (error) {
      return false;
    }
  }

  /**
   * Fermer l'instance exiftool proprement
   * Important à appeler lors de la fermeture de l'application
   */
  async close() {
    try {
      await this.exiftoolInstance.end();
      console.log('ExifTool fermé proprement');
    } catch (error) {
      console.error('Erreur lors de la fermeture d\'ExifTool:', error);
    }
  }
}

module.exports = ExifReader;
