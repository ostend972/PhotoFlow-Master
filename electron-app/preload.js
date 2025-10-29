/**
 * Preload Script - Pont sécurisé entre le processus principal et le renderer
 *
 * Ce script s'exécute dans un contexte privilégié et expose une API sécurisée
 * au renderer via contextBridge. Il empêche l'accès direct à Node.js depuis
 * le renderer pour des raisons de sécurité.
 */

const { contextBridge, ipcRenderer } = require('electron');

// Exposition de l'API au renderer via window.electronAPI
contextBridge.exposeInMainWorld('electronAPI', {
  /**
   * Sélectionner un dossier source
   * @returns {Promise<Object>} Informations sur le dossier sélectionné
   */
  selectFolder: () => ipcRenderer.invoke('select-folder'),

  /**
   * Sélectionner un dossier de destination
   * @returns {Promise<Object>} Chemin et espace disponible
   */
  selectDestination: () => ipcRenderer.invoke('select-destination'),

  /**
   * Détecter automatiquement la date de shooting à partir des EXIF
   * @param {string} folderPath - Chemin du dossier à analyser
   * @returns {Promise<Object>} Date détectée ou erreur
   */
  detectDate: (folderPath) => ipcRenderer.invoke('detect-date', folderPath),

  /**
   * Obtenir des statistiques détaillées sur les sources
   * @param {Array} sources - Liste des sources à analyser
   * @returns {Promise<Object>} Statistiques complètes
   */
  getStatistics: (sources) => ipcRenderer.invoke('get-statistics', sources),

  /**
   * Lancer l'organisation des projets
   * @param {Object} options - Options de traitement
   * @returns {Promise<Object>} Résultats de l'organisation
   */
  organizeProjects: (options) => ipcRenderer.invoke('organize-projects', options),

  /**
   * Ouvrir un dossier dans l'explorateur Windows
   * @param {string} folderPath - Chemin du dossier à ouvrir
   * @returns {Promise<Object>} Succès ou erreur
   */
  openFolder: (folderPath) => ipcRenderer.invoke('open-folder', folderPath),

  /**
   * Récupérer les préférences utilisateur sauvegardées
   * @returns {Promise<Object>} Préférences ou objet vide
   */
  getPreferences: () => ipcRenderer.invoke('get-preferences'),

  /**
   * Sauvegarder les préférences utilisateur
   * @param {Object} preferences - Préférences à sauvegarder
   * @returns {Promise<Object>} Succès ou erreur
   */
  savePreferences: (preferences) => ipcRenderer.invoke('save-preferences', preferences),

  /**
   * Annuler l'opération en cours
   * @returns {Promise<Object>} Confirmation d'annulation
   */
  cancelOperation: () => ipcRenderer.invoke('cancel-operation'),

  // ===== LISTENERS =====

  /**
   * Écouter les messages de log du processus principal
   * @param {Function} callback - Fonction appelée pour chaque message
   */
  onLogMessage: (callback) => {
    ipcRenderer.on('log-message', (event, data) => callback(data));
  },

  /**
   * Écouter les mises à jour de progression
   * @param {Function} callback - Fonction appelée pour chaque mise à jour
   */
  onProgressUpdate: (callback) => {
    ipcRenderer.on('progress-update', (event, data) => callback(data));
  },

  /**
   * Écouter les erreurs du processus principal
   * @param {Function} callback - Fonction appelée en cas d'erreur
   */
  onError: (callback) => {
    ipcRenderer.on('error', (event, data) => callback(data));
  },

  /**
   * Retirer un listener
   * @param {string} channel - Canal à désabonner
   * @param {Function} callback - Fonction de callback à retirer
   */
  removeListener: (channel, callback) => {
    ipcRenderer.removeListener(channel, callback);
  },

  /**
   * Retirer tous les listeners d'un canal
   * @param {string} channel - Canal à nettoyer
   */
  removeAllListeners: (channel) => {
    ipcRenderer.removeAllListeners(channel);
  }
});

// Log de démarrage
console.log('✅ Preload script chargé - API Electron disponible via window.electronAPI');
