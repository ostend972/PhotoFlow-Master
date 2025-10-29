/**
 * PhotoFlow Master - Renderer Process
 * Gestion de l'interface utilisateur et communication avec le processus principal
 */

// État de l'application
const state = {
  sources: [],
  destination: null,
  isProcessing: false,
  config: {
    copyMode: 'copy',
    duplicateStrategy: 'rename',
    verifyIntegrity: false,
    renamePattern: '{original}'
  }
};

// ===== INITIALISATION =====
document.addEventListener('DOMContentLoaded', async () => {
  console.log('🚀 PhotoFlow Master démarré');

  // Charger les préférences
  await loadPreferences();

  // Initialiser les événements
  initializeEvents();

  // Initialiser les listeners IPC
  initializeIPCListeners();

  // Initialiser le drag & drop
  initializeDragAndDrop();

  log('Application prête - Ajoutez vos sources de photos pour commencer', 'info');
});

// ===== ÉVÉNEMENTS =====
function initializeEvents() {
  // Ajouter une source
  document.getElementById('btn-add-source').addEventListener('click', addSource);

  // Sélectionner la destination
  document.getElementById('btn-select-destination').addEventListener('click', selectDestination);

  // Analyser les sources
  document.getElementById('btn-analyze').addEventListener('click', analyzeSourcesHandler);

  // Lancer l'organisation
  document.getElementById('btn-organize').addEventListener('click', organizeProjects);

  // Vider la liste des sources
  document.getElementById('btn-clear-sources').addEventListener('click', clearSources);

  // Effacer le log
  document.getElementById('btn-clear-log').addEventListener('click', clearLog);

  // Annuler l'opération
  document.getElementById('btn-cancel').addEventListener('click', cancelOperation);

  // Modes de copie
  document.querySelectorAll('input[name="copy-mode"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      state.config.copyMode = e.target.value;
      savePreferences();
    });
  });

  // Stratégie de doublons
  document.getElementById('duplicate-strategy').addEventListener('change', (e) => {
    state.config.duplicateStrategy = e.target.value;
    savePreferences();
  });

  // Vérification d'intégrité
  document.getElementById('verify-integrity').addEventListener('change', (e) => {
    state.config.verifyIntegrity = e.target.checked;
    savePreferences();
  });

  // Pattern de renommage
  document.getElementById('rename-pattern').addEventListener('change', (e) => {
    state.config.renamePattern = e.target.value;
    savePreferences();
  });

  // Fermeture du modal
  document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('stats-modal').classList.add('hidden');
    });
  });

  // Fermer modal en cliquant sur l'overlay
  document.querySelector('.modal-overlay').addEventListener('click', () => {
    document.getElementById('stats-modal').classList.add('hidden');
  });
}

// ===== LISTENERS IPC =====
function initializeIPCListeners() {
  // Messages de log
  window.electronAPI.onLogMessage((data) => {
    log(data.message, data.level || 'info');
  });

  // Mises à jour de progression
  window.electronAPI.onProgressUpdate((data) => {
    updateProgress(data);
  });

  // Erreurs
  window.electronAPI.onError((data) => {
    log(`Erreur: ${data.message}`, 'error');
    if (data.details) {
      log(`Détails: ${data.details}`, 'error');
    }
  });
}

// ===== DRAG & DROP =====
function initializeDragAndDrop() {
  const dropZone = document.getElementById('drop-zone');

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
  });

  dropZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
  });

  dropZone.addEventListener('drop', async (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');

    const files = Array.from(e.dataTransfer.files);

    // Filtrer uniquement les dossiers
    for (const file of files) {
      if (file.type === '' || file.type === 'inode/directory') {
        // C'est un dossier
        await addSourceFromPath(file.path);
      }
    }
  });
}

// ===== GESTION DES SOURCES =====
async function addSource() {
  try {
    const result = await window.electronAPI.selectFolder();

    if (result.success && !result.canceled) {
      await addSourceToList(result);
    }
  } catch (error) {
    log(`Erreur lors de l'ajout de la source: ${error.message}`, 'error');
  }
}

async function addSourceFromPath(folderPath) {
  try {
    log(`Analyse du dossier: ${folderPath}`, 'info');

    // Analyser le dossier via IPC
    const result = {
      path: folderPath,
      name: folderPath.split(/[/\\]/).pop(),
      success: true
    };

    // Ajouter à la liste
    await addSourceToList(result);
  } catch (error) {
    log(`Erreur lors de l'ajout du dossier: ${error.message}`, 'error');
  }
}

async function addSourceToList(source) {
  // Vérifier si la source existe déjà
  if (state.sources.find(s => s.path === source.path)) {
    log(`Le dossier ${source.name} est déjà dans la liste`, 'warning');
    return;
  }

  // Ajouter à l'état
  state.sources.push({
    path: source.path,
    name: source.name,
    date: null,
    totalFiles: source.totalFiles || 0,
    totalSize: source.totalSize || 0,
    imageFiles: source.imageFiles || 0
  });

  // Mettre à jour l'affichage
  renderSources();

  // Vérifier si on peut organiser
  updateOrganizeButtonState();

  // Détecter automatiquement la date
  try {
    log(`Détection de la date pour ${source.name}...`, 'info');
    const dateResult = await window.electronAPI.detectDate(source.path);

    if (dateResult.success) {
      // Mettre à jour la date dans l'état
      const sourceInState = state.sources.find(s => s.path === source.path);
      if (sourceInState) {
        sourceInState.date = dateResult.date;
        log(`Date détectée: ${dateResult.formatted} pour ${source.name}`, 'success');
        renderSources();
      }
    } else {
      log(`Aucune date EXIF trouvée pour ${source.name}`, 'warning');
    }
  } catch (error) {
    log(`Erreur lors de la détection de la date: ${error.message}`, 'warning');
  }

  log(`Source ajoutée: ${source.name} (${source.imageFiles || '?'} fichiers images)`, 'success');
}

function renderSources() {
  const container = document.getElementById('sources-list');
  const countBadge = document.getElementById('source-count');

  countBadge.textContent = state.sources.length;

  if (state.sources.length === 0) {
    container.innerHTML = '<div class="info-text">Aucune source ajoutée</div>';
    return;
  }

  container.innerHTML = state.sources.map((source, index) => `
    <div class="source-item">
      <div class="source-header">
        <div>
          <div class="source-name">${escapeHtml(source.name)}</div>
          <div class="source-path">${escapeHtml(source.path)}</div>
        </div>
        <div class="source-actions">
          <button class="btn-icon" onclick="removeSource(${index})" title="Supprimer">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
          </button>
        </div>
      </div>
      <div class="source-info">
        <div>📸 ${source.imageFiles || '?'} fichiers images</div>
        <div>💾 ${formatBytes(source.totalSize || 0)}</div>
        <div>📅 ${source.date ? formatDate(source.date) : 'Date non détectée'}</div>
      </div>
    </div>
  `).join('');
}

function removeSource(index) {
  const source = state.sources[index];
  state.sources.splice(index, 1);
  renderSources();
  updateOrganizeButtonState();
  log(`Source supprimée: ${source.name}`, 'info');
}

function clearSources() {
  if (state.sources.length === 0) return;

  if (confirm(`Voulez-vous vraiment vider la liste des ${state.sources.length} source(s) ?`)) {
    state.sources = [];
    renderSources();
    updateOrganizeButtonState();
    log('Liste des sources vidée', 'info');
  }
}

// Rendre removeSource accessible globalement
window.removeSource = removeSource;

// ===== DESTINATION =====
async function selectDestination() {
  try {
    const result = await window.electronAPI.selectDestination();

    if (result.success && !result.canceled) {
      state.destination = result.path;

      // Mettre à jour l'interface
      document.getElementById('destination-path').value = result.path;

      // Afficher l'espace disque
      const infoEl = document.getElementById('disk-space-info');
      infoEl.classList.remove('hidden');
      infoEl.textContent = `💾 Espace disponible: ${formatBytes(result.freeSpace)}`;

      updateOrganizeButtonState();
      log(`Destination sélectionnée: ${result.path}`, 'success');
    }
  } catch (error) {
    log(`Erreur lors de la sélection de la destination: ${error.message}`, 'error');
  }
}

// ===== STATISTIQUES =====
async function analyzeSourcesHandler() {
  if (state.sources.length === 0) {
    log('Aucune source à analyser', 'warning');
    return;
  }

  log('Analyse des sources en cours...', 'info');

  try {
    const result = await window.electronAPI.getStatistics(state.sources);

    if (result.success) {
      displayStatistics(result);
    } else {
      log(`Erreur lors de l'analyse: ${result.error}`, 'error');
    }
  } catch (error) {
    log(`Erreur lors de l'analyse: ${error.message}`, 'error');
  }
}

function displayStatistics(stats) {
  const modal = document.getElementById('stats-modal');
  const content = document.getElementById('stats-content');

  // Créer le contenu HTML des statistiques
  const fileTypesList = Object.entries(stats.fileTypeStats || {})
    .sort((a, b) => b[1] - a[1])
    .map(([ext, count]) => `
      <div style="display: flex; justify-content: space-between; padding: 0.5rem; background: var(--bg-darker); margin-bottom: 0.25rem; border-radius: 4px;">
        <span>${ext}</span>
        <span style="color: var(--primary);">${count} fichiers</span>
      </div>
    `).join('');

  const sourcesList = (stats.filesBySource || []).map(source => `
    <div style="padding: 0.75rem; background: var(--bg-darker); margin-bottom: 0.5rem; border-radius: 6px;">
      <div style="font-weight: 600; margin-bottom: 0.25rem;">${escapeHtml(source.name)}</div>
      <div style="font-size: 0.85rem; color: var(--text-secondary);">
        ${source.files} fichiers - ${formatBytes(source.size)}
      </div>
    </div>
  `).join('');

  content.innerHTML = `
    <div style="display: grid; gap: 1.5rem;">
      <div class="config-section">
        <h3>Vue d'ensemble</h3>
        <div style="background: var(--bg-darker); padding: 1rem; border-radius: 8px;">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div>
              <div style="color: var(--text-secondary); font-size: 0.85rem;">Projets</div>
              <div style="font-size: 1.5rem; font-weight: 700; color: var(--primary);">${stats.filesBySource?.length || 0}</div>
            </div>
            <div>
              <div style="color: var(--text-secondary); font-size: 0.85rem;">Fichiers totaux</div>
              <div style="font-size: 1.5rem; font-weight: 700; color: var(--primary);">${stats.totalFiles || 0}</div>
            </div>
          </div>
          <div style="margin-top: 1rem;">
            <div style="color: var(--text-secondary); font-size: 0.85rem;">Taille totale</div>
            <div style="font-size: 1.3rem; font-weight: 700; color: var(--success);">${formatBytes(stats.totalSize || 0)}</div>
          </div>
        </div>
      </div>

      <div class="config-section">
        <h3>Répartition par type</h3>
        ${fileTypesList}
      </div>

      <div class="config-section">
        <h3>Par source</h3>
        ${sourcesList}
      </div>
    </div>
  `;

  modal.classList.remove('hidden');
  log('Analyse terminée', 'success');
}

// ===== ORGANISATION DES PROJETS =====
async function organizeProjects() {
  if (state.isProcessing) {
    log('Un traitement est déjà en cours', 'warning');
    return;
  }

  if (state.sources.length === 0) {
    log('Aucune source à traiter', 'warning');
    return;
  }

  if (!state.destination) {
    log('Veuillez sélectionner un dossier de destination', 'warning');
    return;
  }

  // Confirmation
  const confirmMsg = `Lancer l'organisation de ${state.sources.length} projet(s) ?\n\nMode: ${state.config.copyMode}\nDestination: ${state.destination}`;
  if (!confirm(confirmMsg)) {
    return;
  }

  state.isProcessing = true;
  updateUI Processing(true);

  log('🚀 Début de l\'organisation des projets...', 'info');

  try {
    const result = await window.electronAPI.organizeProjects({
      sources: state.sources,
      destination: state.destination,
      copyMode: state.config.copyMode,
      duplicateStrategy: state.config.duplicateStrategy,
      verifyIntegrity: state.config.verifyIntegrity,
      renamePattern: state.config.renamePattern
    });

    if (result.success) {
      log(`✨ Organisation terminée! ${result.totalProcessed} fichiers traités`, 'success');

      if (result.totalErrors > 0) {
        log(`⚠️ ${result.totalErrors} erreur(s) rencontrée(s)`, 'warning');
      }

      // Afficher un résumé
      showCompletionSummary(result);
    } else {
      log(`❌ Erreur: ${result.error}`, 'error');
    }
  } catch (error) {
    log(`❌ Erreur fatale: ${error.message}`, 'error');
  } finally {
    state.isProcessing = false;
    updateUIProcessing(false);
  }
}

function showCompletionSummary(result) {
  const resultsList = result.results.map(r =>
    `• ${r.source}: ${r.processed} fichiers traités${r.errors > 0 ? `, ${r.errors} erreur(s)` : ''}`
  ).join('\n');

  alert(`Organisation terminée!\n\n${resultsList}\n\nTotal: ${result.totalProcessed} fichiers`);
}

async function cancelOperation() {
  if (confirm('Voulez-vous vraiment annuler l\'opération en cours ?')) {
    log('Annulation demandée...', 'warning');
    await window.electronAPI.cancelOperation();
  }
}

// ===== GESTION DE LA PROGRESSION =====
function updateProgress(data) {
  const progressContainer = document.getElementById('progress-container');
  const progressBar = document.getElementById('progress-bar');
  const progressLabel = document.getElementById('progress-label');
  const progressDetails = document.getElementById('progress-details');

  progressContainer.classList.remove('hidden');

  if (data.type === 'global') {
    const percent = ((data.current / data.total) * 100).toFixed(0);
    progressBar.style.width = `${percent}%`;
    progressBar.textContent = `${percent}%`;
    progressLabel.textContent = `Projet ${data.current + 1}/${data.total}: ${data.currentProject}`;
  } else if (data.type === 'file') {
    const percent = ((data.current / data.total) * 100).toFixed(0);
    progressBar.style.width = `${percent}%`;
    progressBar.textContent = `${percent}%`;
    progressDetails.textContent = `${data.current}/${data.total} fichiers - ${data.filename}`;
  }
}

function updateUIProcessing(isProcessing) {
  const btnOrganize = document.getElementById('btn-organize');
  const btnCancel = document.getElementById('btn-cancel');
  const progressContainer = document.getElementById('progress-container');

  if (isProcessing) {
    btnOrganize.disabled = true;
    btnCancel.classList.remove('hidden');
    progressContainer.classList.remove('hidden');
  } else {
    btnOrganize.disabled = false;
    btnCancel.classList.add('hidden');
    progressContainer.classList.add('hidden');
  }
}

function updateOrganizeButtonState() {
  const btnOrganize = document.getElementById('btn-organize');
  const canOrganize = state.sources.length > 0 && state.destination !== null;

  btnOrganize.disabled = !canOrganize;
}

// ===== LOGGING =====
function log(message, level = 'info') {
  const container = document.getElementById('log-container');
  const entry = document.createElement('div');
  entry.className = `log-entry ${level}`;

  const timestamp = new Date().toLocaleTimeString('fr-FR');

  entry.innerHTML = `
    <div class="log-timestamp">${timestamp}</div>
    <div class="log-message">${escapeHtml(message)}</div>
  `;

  container.appendChild(entry);
  container.scrollTop = container.scrollHeight;

  // Limiter à 100 entrées
  while (container.children.length > 100) {
    container.removeChild(container.firstChild);
  }
}

function clearLog() {
  const container = document.getElementById('log-container');
  container.innerHTML = '';
  log('Journal effacé', 'info');
}

// ===== PRÉFÉRENCES =====
async function loadPreferences() {
  try {
    const result = await window.electronAPI.getPreferences();

    if (result.success && result.preferences) {
      const prefs = result.preferences;

      // Restaurer les préférences
      if (prefs.copyMode) {
        state.config.copyMode = prefs.copyMode;
        document.querySelector(`input[name="copy-mode"][value="${prefs.copyMode}"]`).checked = true;
      }

      if (prefs.duplicateStrategy) {
        state.config.duplicateStrategy = prefs.duplicateStrategy;
        document.getElementById('duplicate-strategy').value = prefs.duplicateStrategy;
      }

      if (prefs.verifyIntegrity !== undefined) {
        state.config.verifyIntegrity = prefs.verifyIntegrity;
        document.getElementById('verify-integrity').checked = prefs.verifyIntegrity;
      }

      if (prefs.renamePattern) {
        state.config.renamePattern = prefs.renamePattern;
        document.getElementById('rename-pattern').value = prefs.renamePattern;
      }

      if (prefs.lastDestination) {
        state.destination = prefs.lastDestination;
        document.getElementById('destination-path').value = prefs.lastDestination;
      }

      console.log('Préférences chargées');
    }
  } catch (error) {
    console.error('Erreur lors du chargement des préférences:', error);
  }
}

async function savePreferences() {
  try {
    const preferences = {
      copyMode: state.config.copyMode,
      duplicateStrategy: state.config.duplicateStrategy,
      verifyIntegrity: state.config.verifyIntegrity,
      renamePattern: state.config.renamePattern,
      lastDestination: state.destination
    };

    await window.electronAPI.savePreferences(preferences);
  } catch (error) {
    console.error('Erreur lors de la sauvegarde des préférences:', error);
  }
}

// ===== UTILITAIRES =====
function formatBytes(bytes) {
  if (bytes === 0) return '0 B';

  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString) {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  } catch {
    return dateString;
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
