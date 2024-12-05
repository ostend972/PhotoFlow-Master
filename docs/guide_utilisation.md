# 📸 Guide d'Utilisation PhotoFlow Master

## 🎯 Introduction

PhotoFlow Master est un outil professionnel conçu pour organiser automatiquement vos projets photographiques. Ce guide vous accompagnera pas à pas dans son utilisation.

## 💻 Configuration Requise

- Python 3.8 ou plus récent
- Espace disque : 100 Mo minimum
- Systèmes supportés : Windows 10/11, MacOS

## 🚀 Démarrage

1. **Lancement du programme**
   ```bash
   python src/photoflow.py
   ```

2. **Sélection des Sources**
   - Entrez le chemin complet du dossier source
   - Donnez un nom unique à chaque projet
   - Appuyez sur Entrée sans texte pour terminer

## 📁 Structure des Dossiers

```
PROJET_PHOTO/
├── 01_PRE-PRODUCTION/
│   ├── Moodboard/
│   ├── References/
│   └── Brief/
├── 02_RAW/
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

## 🎨 Fonctionnalités Détaillées

**Détection de Date**
- Extraction automatique depuis les métadonnées EXIF
- Option de saisie manuelle si non détectée

**Organisation Multi-Sources**
- Traitement simultané de plusieurs dossiers
- Création de projets indépendants
- Conservation de la structure originale

**Gestion des Fichiers**
- Copie sécurisée des fichiers
- Maintien des métadonnées
- Journal des opérations

## ⚠️ Résolution des Problèmes

**Erreur de Chemin**
- Vérifiez que le chemin existe
- Utilisez des chemins absolus
- Évitez les caractères spéciaux

**Problème de Permissions**
- Lancez le programme en administrateur
- Vérifiez les droits d'accès aux dossiers

## 📞 Support

Pour toute question ou problème :
- Consultez les issues GitHub
- Créez un ticket si nécessaire
- Décrivez précisément votre problème

---

*Documentation mise à jour le 05/12/2024*
