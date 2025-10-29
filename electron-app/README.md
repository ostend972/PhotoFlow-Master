# 📸 PhotoFlow Master - Application Electron

Application desktop professionnelle pour l'organisation automatique de projets photo, développée avec Electron pour Windows.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Electron](https://img.shields.io/badge/electron-28.0.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

---

## 🎯 Caractéristiques Principales

### ✨ Fonctionnalités

- **Organisation Automatique** : Création de structures de dossiers professionnelles
- **Détection EXIF** : Extraction automatique des dates de prise de vue
- **Drag & Drop** : Interface intuitive avec glisser-déposer
- **Multi-sources** : Gestion de plusieurs dossiers sources simultanément
- **Modes Flexibles** : Copie, déplacement ou liens symboliques
- **Progression en Temps Réel** : Barre de progression et journal détaillé
- **Gestion des Doublons** : Stratégies configurables (renommer, ignorer, remplacer)
- **Vérification d'Intégrité** : Checksum MD5 optionnel
- **Sauvegarde des Préférences** : Mémorisation des paramètres

### 📂 Structure de Projet Créée

```
PROJETS_PHOTO/
└── ANNÉE/
    └── DATE_NOM_PROJET/
        ├── 01_PRE-PRODUCTION/
        │   ├── Moodboard/
        │   ├── References/
        │   ├── Brief/
        │   └── Planning/
        ├── 02_RAW/ (photos sources)
        ├── 03_SELECTS/
        │   ├── First_Pass/
        │   └── Final_Selection/
        ├── 04_RETOUCHE/
        │   ├── PSD/
        │   ├── FINALS/
        │   └── Client_Review/
        ├── 05_VIDEO/
        │   ├── RUSH/
        │   ├── EDITS/
        │   └── FINALS/
        └── 06_ADMIN/
            ├── Factures/
            ├── Contrats/
            ├── Correspondance/
            └── Releases/
```

---

## 📋 Prérequis

### Système d'Exploitation
- **Windows 10/11** (x64 ou x86)
- **4 GB RAM minimum** (8 GB recommandé)
- **500 MB d'espace disque** pour l'application

### Développement
- **Node.js 18.x ou supérieur** ([Télécharger](https://nodejs.org/))
- **npm 9.x ou supérieur** (inclus avec Node.js)
- **Python 3.x** (pour certaines dépendances natives)
- **Visual Studio Build Tools** (Windows uniquement)

### Vérifier les Versions

```bash
node --version   # devrait afficher v18.x.x ou supérieur
npm --version    # devrait afficher 9.x.x ou supérieur
```

---

## 🚀 Installation

### 1️⃣ Cloner le Projet

```bash
git clone <url-du-repo>
cd PhotoFlow-Master/electron-app
```

### 2️⃣ Installer les Dépendances

```bash
npm install
```

Cette commande installera :
- **Electron** : Framework pour l'application desktop
- **exiftool-vendored** : Lecture des métadonnées EXIF
- **sharp** : Traitement d'images rapide
- **fs-extra** : Opérations fichiers avancées
- **date-fns** : Manipulation des dates
- **glob** : Recherche de fichiers par patterns
- **electron-builder** : Création de l'exécutable

**⏱️ Temps d'installation** : 2-5 minutes selon votre connexion

### 3️⃣ Vérifier l'Installation

```bash
npm run start
```

L'application devrait se lancer et afficher l'interface principale.

---

## 💻 Développement

### Lancer en Mode Développement

```bash
npm run dev
```

Cette commande lance l'application avec :
- **Console de développement** ouverte automatiquement
- **Hot reload** sur les modifications de fichiers
- **Messages de debug** dans la console

### Structure du Projet

```
electron-app/
├── main.js               # Processus principal Electron
├── preload.js            # Script preload (pont IPC)
├── package.json          # Configuration npm et build
│
├── renderer/             # Interface utilisateur
│   ├── index.html        # Structure HTML
│   ├── styles.css        # Styles CSS
│   └── renderer.js       # Logique frontend
│
├── src/                  # Modules métier
│   ├── fileOperations.js # Gestion des fichiers
│   ├── exifReader.js     # Lecture EXIF
│   └── projectStructure.js # Création structure
│
└── assets/               # Ressources (icônes, etc.)
```

### Architecture Electron

#### Processus Principal (main.js)
- Crée et gère la fenêtre de l'application
- Gère les opérations fichiers (sécurité)
- Communique avec le renderer via IPC
- Accès complet à Node.js et au système

#### Processus Renderer (renderer/)
- Interface utilisateur (HTML/CSS/JS)
- Interagit avec l'utilisateur
- Accès limité pour la sécurité
- Communique avec main via IPC

#### Preload Script (preload.js)
- Pont sécurisé entre main et renderer
- Expose une API contrôlée au renderer
- Prévient les failles de sécurité

### IPC (Inter-Process Communication)

```javascript
// Dans le renderer (interface)
const result = await window.electronAPI.selectFolder();

// ↓ IPC via preload.js ↓

// Dans le main (backend)
ipcMain.handle('select-folder', async (event) => {
  // Logique de sélection de dossier
  return { success: true, path: '...' };
});
```

---

## 📦 Build (Création de l'Exécutable)

### Build Windows (64-bit)

```bash
npm run build:win
```

### Build Windows (32-bit)

```bash
npm run build:win32
```

### Build pour Toutes les Architectures

```bash
npm run dist
```

### Résultats du Build

Les fichiers seront créés dans le dossier `dist/` :

```
dist/
├── PhotoFlow Master-1.0.0-x64.exe      # Installateur 64-bit
├── PhotoFlow Master-1.0.0-ia32.exe     # Installateur 32-bit
├── PhotoFlow Master-1.0.0-x64-portable.exe  # Version portable
└── win-unpacked/                        # Version non empaquetée
```

### Taille des Fichiers
- **Installateur** : ~100-150 MB
- **Application installée** : ~200-250 MB

### Options d'Installation (NSIS)
- Installation personnalisée (dossier modifiable)
- Raccourci bureau
- Raccourci menu démarrer
- Désinstalleur inclus

---

## 🎮 Utilisation

### Démarrage Rapide

1. **Lancez l'application**
   - Double-cliquez sur `PhotoFlow Master.exe`
   - Ou lancez depuis le menu démarrer

2. **Ajoutez des sources**
   - Cliquez sur "Ajouter un Dossier"
   - Ou glissez-déposez des dossiers dans la zone prévue
   - Les dates EXIF sont détectées automatiquement

3. **Sélectionnez une destination**
   - Cliquez sur "Parcourir" dans la section Destination
   - Choisissez le disque où créer les projets

4. **Configurez les options** (optionnel)
   - Mode d'opération (copier/déplacer/liens)
   - Gestion des doublons
   - Vérification d'intégrité
   - Pattern de renommage

5. **Analysez** (optionnel)
   - Cliquez sur "Analyser les Sources"
   - Visualisez les statistiques détaillées

6. **Lancez l'organisation**
   - Cliquez sur "Lancer l'Organisation"
   - Suivez la progression en temps réel
   - Consultez le journal d'activité

### Fonctionnalités Avancées

#### Patterns de Renommage
- `{original}` : Conserve le nom original
- `{date}_{original}` : Préfixe avec la date (2025-10-29_photo.jpg)
- `{project}_{counter:04d}` : Nom de projet + compteur (Mariage_0001.jpg)
- `{date}_{project}_{counter:04d}` : Combinaison complète

#### Gestion des Doublons
- **Renommer** : Ajoute _1, _2, etc.
- **Ignorer** : Ne copie pas les fichiers existants
- **Remplacer** : Écrase les fichiers existants

#### Vérification d'Intégrité
- Active le calcul de checksum MD5
- Vérifie que les fichiers copiés sont identiques
- Légère baisse de performance mais sécurité maximale

---

## 🔧 Dépannage

### Problèmes Courants

#### L'application ne démarre pas

**Symptôme** : Double-clic sans effet

**Solutions** :
1. Vérifier que Node.js est installé : `node --version`
2. Réinstaller les dépendances : `npm install`
3. Vérifier les logs dans `%APPDATA%/PhotoFlow Master/logs/`

#### Erreur "Cannot find module"

**Symptôme** : Message d'erreur au démarrage

**Solution** :
```bash
rm -rf node_modules
npm install
```

#### ExifTool ne fonctionne pas

**Symptôme** : Dates EXIF non détectées

**Solution** :
```bash
npm install exiftool-vendored --force
```

#### Build échoue

**Symptôme** : Erreur pendant `npm run build`

**Solutions** :
1. Installer Visual Studio Build Tools (Windows)
2. Vérifier l'espace disque disponible (>2 GB)
3. Nettoyer le cache : `npm cache clean --force`

### Logs et Débogage

#### Localisation des Logs

**Windows** :
```
C:\Users\<Username>\AppData\Roaming\PhotoFlow Master\logs\
```

#### Activer le Mode Debug

```bash
npm run dev
```

Puis ouvrir la console de développement avec `Ctrl+Shift+I`

#### Logs dans l'Application

Le journal d'activité dans l'interface enregistre :
- ✅ Opérations réussies
- ⚠️ Avertissements
- ❌ Erreurs détaillées
- 📊 Statistiques de traitement

---

## 🏗️ Architecture Technique

### Technologies Utilisées

| Technologie | Version | Usage |
|-------------|---------|-------|
| Electron | 28.0.0 | Framework desktop |
| Node.js | 18+ | Runtime JavaScript |
| ExifTool | 25.0.0 | Lecture métadonnées |
| Sharp | 0.33.0 | Traitement d'images |
| fs-extra | 11.2.0 | Opérations fichiers |
| date-fns | 3.0.6 | Manipulation dates |

### Choix d'Architecture

#### Pourquoi Electron ?
- ✅ Multi-plateforme (Windows, macOS, Linux)
- ✅ Technologies web familières (HTML/CSS/JS)
- ✅ Accès complet au système de fichiers
- ✅ Grande communauté et écosystème riche
- ✅ Mises à jour faciles

#### Sécurité
- **Context Isolation** : Séparation processus main/renderer
- **No Node Integration** : Pas d'accès direct à Node.js depuis l'UI
- **Preload Script** : API contrôlée et sécurisée
- **Content Security Policy** : Protection contre XSS

#### Performance
- **Traitement asynchrone** : Interface non bloquante
- **Streaming** : Traitement fichiers par chunks
- **Worker threads** : Disponible pour calculs intensifs
- **Caching** : Préférences et résultats intermédiaires

---

## 📝 Développement Futur

### Fonctionnalités Planifiées

#### Version 1.1
- [ ] Prévisualisation des images avant organisation
- [ ] Export de rapports PDF
- [ ] Templates de structure personnalisables
- [ ] Mode sombre/clair

#### Version 1.2
- [ ] Synchronisation cloud optionnelle
- [ ] Backup automatique
- [ ] Analyse de doublons intelligente
- [ ] Suggestions de nommage AI

#### Version 2.0
- [ ] Éditeur EXIF intégré
- [ ] Gestion des collections
- [ ] Partage client intégré
- [ ] Plugin system

---

## 🤝 Contribution

### Comment Contribuer

1. **Fork** le projet
2. Créez une **branche** : `git checkout -b feature/AmazingFeature`
3. **Committez** : `git commit -m 'Add AmazingFeature'`
4. **Push** : `git push origin feature/AmazingFeature`
5. Ouvrez une **Pull Request**

### Guidelines

- Code commenté en français
- Tests pour les nouvelles fonctionnalités
- Documentation à jour
- Respect des conventions de code

---

## 📄 Licence

Ce projet est sous licence **MIT**. Voir le fichier `LICENSE` pour plus de détails.

---

## 👥 Auteurs

- **PhotoFlow Master Team**
- Développé avec ❤️ pour les photographes professionnels

---

## 📞 Support

### Obtenir de l'Aide

- 📧 Email : support@photoflow-master.com
- 💬 Discord : [Rejoindre la communauté](#)
- 🐛 Issues : [GitHub Issues](#)
- 📖 Documentation : [Wiki complet](#)

### Questions Fréquentes

**Q : L'application fonctionne-t-elle hors ligne ?**
R : Oui, 100% hors ligne. Aucune connexion internet nécessaire.

**Q : Puis-je traiter plusieurs milliers de photos ?**
R : Oui, l'application est optimisée pour de gros volumes.

**Q : Les fichiers originaux sont-ils modifiés ?**
R : Non, jamais. En mode "Copier", les originaux restent intacts.

**Q : Quels formats d'images sont supportés ?**
R : JPG, PNG, TIFF, RAW (ARW, CR2, NEF, RAF, DNG), HEIC, WebP, BMP

**Q : Comment mettre à jour l'application ?**
R : Téléchargez la dernière version et installez-la par-dessus.

---

## 🙏 Remerciements

- **Electron** pour le framework
- **ExifTool** pour la lecture EXIF
- **Sharp** pour le traitement d'images
- La communauté des photographes pour les retours

---

## 📊 Statistiques

- ⭐ Stars : 0
- 🍴 Forks : 0
- 🐛 Issues : 0
- 📥 Téléchargements : 0

---

**Fait avec 📸 et ☕ par des passionnés de photographie**

