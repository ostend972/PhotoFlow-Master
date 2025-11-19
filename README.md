# 📸 PhotoFlow Master v2.0

**Professional Photo Project Manager** - Automated organization and workflow optimization for photographers.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Quality](https://img.shields.io/badge/code%20quality-A+-brightgreen.svg)](https://github.com/ostend972/PhotoFlow-Master)

> Transformez le chaos de vos projets photo en une organisation parfaite en quelques clics !

## ✨ Fonctionnalités

- **🔍 Détection EXIF Intelligente**: Extraction automatique des dates de prise de vue (RAW + JPEG)
- **📁 Structure Professionnelle**: Création de dossiers standardisés pour vos projets
- **⚡ Traitement Concurrent**: Copie rapide avec multi-threading
- **🎯 Gestion des Collisions**: Résolution automatique des conflits de noms
- **💾 Validation d'Espace**: Vérification de l'espace disque avant traitement
- **🖥️ Double Interface**: CLI moderne et GUI intuitive
- **📊 Suivi en Temps Réel**: Feedback détaillé sur les opérations
- **🧪 Testé à 90%+**: Suite de tests complète avec pytest

## 🚀 Installation Rapide

```bash
# Cloner le dépôt
git clone https://github.com/ostend972/PhotoFlow-Master.git
cd PhotoFlow-Master

# Installer les dépendances
pip install -r requirements.txt

# Ou avec les dépendances de développement
pip install -e ".[dev]"
```

## 💫 Utilisation

### Interface en Ligne de Commande

```bash
python src/photoflow_cli.py
```

### Interface Graphique

```bash
python src/photoflow_gui_improved.py
```

### Utilisation Programmatique

```python
from photoflow import PhotoFlowManager, SourceInfo
from pathlib import Path

# Initialiser le gestionnaire
manager = PhotoFlowManager()

# Créer une source
source = SourceInfo(
    path=Path("/photos/mariage"),
    name="Mariage_Dupont",
    date="2023-12-31"  # Ou None pour détection auto
)

# Créer le projet
result = manager.create_project(source, Path("/D:"))

print(f"Succès: {result.success}")
print(f"Fichiers copiés: {result.files_copied}")
print(f"Chemin projet: {result.project_path}")
```

## 📁 Structure de Projet

PhotoFlow crée automatiquement cette structure :

```
DISQUE/PROJETS_PHOTO/ANNEE/YYYY-MM-DD_NomProjet/
├── 01_PRE-PRODUCTION/
│   ├── Moodboard/
│   ├── References/
│   └── Brief/
├── 02_RAW/              # Fichiers sources copiés ici
├── 03_SELECTS/
├── 04_RETOUCHE/
│   ├── PSD/
│   └── FINALS/
├── 05_VIDEO/
│   ├── RUSH/
│   └── FINALS/
└── 06_ADMIN/
    ├── Factures/
    └── Contrats/
```

## 📷 Formats Supportés

**Formats RAW:**
- Sony: `.ARW`
- Canon: `.CR2`, `.CR3`
- Nikon: `.NEF`
- Fujifilm: `.RAF`
- Adobe/Universal: `.DNG`
- Olympus: `.ORF`
- Panasonic: `.RW2`

**Formats Traités:**
- `.JPG`, `.JPEG`
- `.TIFF`, `.TIF`
- `.PNG`

## 🏗️ Architecture

### Organisation des Modules

```
src/photoflow/
├── __init__.py           # Exports du package
├── constants.py          # Constantes de configuration
├── exceptions.py         # Exceptions personnalisées
├── validators.py         # Validation des entrées
├── exif_handler.py       # Extraction EXIF
├── file_manager.py       # Opérations sur fichiers
├── core.py              # Logique métier principale
└── logging_config.py    # Configuration logging
```

### Patterns de Conception

- **Dataclasses**: `SourceInfo`, `ProjectResult`, `CopyResult`
- **Injection de Dépendances**: Handlers personnalisables
- **Factory**: Création de structure de projet
- **Observer**: Callbacks de progression
- **Strategy**: Validation et sanitization modulaires

## 🧪 Tests

Exécuter la suite de tests :

```bash
# Tous les tests
pytest

# Avec couverture
pytest --cov=src/photoflow --cov-report=html

# Tests spécifiques
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

## 🛠️ Développement

### Configuration de l'Environnement

```bash
# Installer avec dépendances dev
pip install -e ".[dev]"

# Vérification des types
mypy src/

# Linting
ruff check src/

# Formatage
ruff format src/
```

### Standards de Qualité

- **Type Hints**: Annotations complètes obligatoires
- **Docstrings**: Format Google pour toutes les APIs publiques
- **Couverture**: Minimum 90% requis
- **Gestion d'Erreurs**: Exceptions spécifiques, pas de `except` nu
- **Performance**: Générateurs pour gros volumes
- **Sécurité**: Validation de chemins, pas d'injection

## 📊 Performance

### Benchmarks

| Opération | Fichiers | Temps | Notes |
|-----------|----------|-------|-------|
| Extraction EXIF | 1 000 | ~2s | Avec cache LRU |
| Copie Fichiers | 1 000 (10GB) | ~30s | 4 workers concurrents |
| Création Projet | 1 | <1s | Structure seule |

### Optimisations

- Augmenter `MAX_WORKERS` dans `constants.py` pour SSD rapides
- Ajuster `EXIF_CACHE_SIZE` pour gros lots
- Utiliser `auto_detect_dates=False` si dates pré-remplies

## 🐛 Dépannage

### Problèmes Courants

**Date EXIF non trouvée:**
- Vérifier que les images ont le tag `DateTimeOriginal`
- Ouvrir dans un visualiseur EXIF pour vérifier
- Utiliser la saisie manuelle en dernier recours

**Erreurs de permission:**
- Exécuter avec permissions appropriées
- Vérifier que l'antivirus ne bloque pas
- Vérifier que le disque de destination est accessible en écriture

**Problèmes mémoire avec gros dossiers:**
- Le traitement utilise des générateurs
- Vérifier RAM disponible si 10 000+ fichiers
- Envisager de traiter en lots plus petits

## 📝 Changelog

### v2.0.0 (2025-11-16)

**Refonte Majeure:**
- Réécriture complète avec patterns Python modernes
- Ajout de type hints complets
- Hiérarchie d'exceptions personnalisées
- Architecture modulaire
- Suite de tests complète (90%+ couverture)
- Gestion d'erreurs améliorée
- Opérations concurrentes sur fichiers
- Cache EXIF pour performance
- GUI thread-safe avec pattern message queue
- Sécurité renforcée avec validation de chemins

**Corrections de Bugs:**
- Gestion des collisions de fichiers
- Remplacement de l'API `_getexif()` dépréciée
- Logique de boucle dans saisie sources
- Nettoyage approprié des ressources

### v1.0.0

- Version initiale

## 🤝 Contribution

Les contributions sont bienvenues ! Merci de :

1. Fork le dépôt
2. Créer une branche feature
3. Ajouter des tests pour les nouvelles fonctionnalités
4. S'assurer que tous les tests passent
5. Soumettre une pull request

## 📄 Licence

MIT License - voir le fichier [LICENSE](LICENSE) pour détails.

## 👥 Auteurs

- **CLERENCE Alan** - Photographe Professionnel & Développeur
- PhotoFlow Team

## 🙏 Remerciements

- Construit avec [Pillow](https://python-pillow.org/) pour le traitement d'images
- [Rich](https://rich.readthedocs.io/) pour l'interface CLI
- [psutil](https://github.com/giampaolo/psutil) pour les utilitaires système

---

⭐️ **Si ce projet vous aide, n'hésitez pas à lui donner une étoile !**

**Fait avec ❤️ pour les photographes**
