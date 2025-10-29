#!/usr/bin/env python3
"""
PhotoFlow Master - Interface Graphique Avancée
Gestionnaire professionnel de projets photo avec interface GUI
Version améliorée avec fonctionnalités avancées
"""

from pathlib import Path
from datetime import datetime
import re
import shutil
import logging
import psutil
import threading
import hashlib
import zipfile
import locale
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from PIL import Image
from PIL.ExifTags import TAGS
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from time import time


class PhotoProManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📸 PhotoFlow Master Pro - Gestionnaire de Projets Photo")
        self.root.geometry("1100x800")
        self.root.resizable(True, True)

        # Variables principales
        self.sources = []  # Liste de dictionnaires: {'path': Path, 'name': str, 'date': str}
        self.selected_drive = None
        self.cancel_flag = False

        # Configuration des options
        self.copy_mode = tk.StringVar(value="copy")  # copy, move, symlink, compress
        self.duplicate_strategy = tk.StringVar(value="rename")  # rename, skip, replace
        self.verify_integrity = tk.BooleanVar(value=False)
        self.detect_corrupted = tk.BooleanVar(value=True)
        self.confirm_overwrite = tk.BooleanVar(value=True)
        self.use_multithread = tk.BooleanVar(value=True)
        self.max_threads = tk.IntVar(value=4)
        self.rename_pattern = tk.StringVar(value="{original}")  # {original}, {date}_{original}, etc.

        # Filtres de fichiers
        self.file_filters = {
            '.ARW': tk.BooleanVar(value=True),
            '.CR2': tk.BooleanVar(value=True),
            '.NEF': tk.BooleanVar(value=True),
            '.RAF': tk.BooleanVar(value=True),
            '.DNG': tk.BooleanVar(value=True),
            '.JPG': tk.BooleanVar(value=True),
            '.JPEG': tk.BooleanVar(value=True),
            '.TIFF': tk.BooleanVar(value=True),
            '.PNG': tk.BooleanVar(value=True),
            '.HEIC': tk.BooleanVar(value=True),
        }

        # Formats de date supportés
        self.date_formats = [
            ("%d-%m-%Y", "JJ-MM-AAAA"),
            ("%m-%d-%Y", "MM-JJ-AAAA"),
            ("%Y-%m-%d", "AAAA-MM-JJ"),
            ("%d/%m/%Y", "JJ/MM/AAAA"),
            ("%m/%d/%Y", "MM/JJ/AAAA"),
        ]
        self.current_date_format = tk.StringVar(value=self.date_formats[0][0])

        # Statistiques de traitement
        self.stats = {
            'total_files': 0,
            'total_size': 0,
            'processed_files': 0,
            'processed_size': 0,
            'start_time': None,
            'file_types': defaultdict(int),
        }

        # Configuration du logging
        self.setup_logging()

        # Configuration du style
        self.setup_style()

        # Création de l'interface
        self.create_widgets()

        # Configuration de la localisation
        try:
            locale.setlocale(locale.LC_ALL, '')
        except:
            pass

    def setup_logging(self):
        """Configure le système de logging"""
        log_dir = Path.home() / "Documents" / "PhotoProManager" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"manager_{datetime.now().strftime('%Y%m%d')}.log"
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger()

    def setup_style(self):
        """Configure le style de l'interface"""
        style = ttk.Style()
        style.theme_use('clam')

        # Couleurs personnalisées
        style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'), foreground='#2c3e50')
        style.configure('Subtitle.TLabel', font=('Helvetica', 10, 'italic'), foreground='#7f8c8d')
        style.configure('Header.TLabel', font=('Helvetica', 12, 'bold'), foreground='#34495e')
        style.configure('Action.TButton', font=('Helvetica', 10), padding=10)
        style.configure('Danger.TButton', font=('Helvetica', 10), background='#e74c3c', foreground='white')

    def create_widgets(self):
        """Crée tous les widgets de l'interface"""
        # Notebook pour onglets
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Onglet principal
        main_tab = ttk.Frame(self.notebook)
        self.notebook.add(main_tab, text="📂 Organisation")
        self.create_main_tab(main_tab)

        # Onglet options avancées
        options_tab = ttk.Frame(self.notebook)
        self.notebook.add(options_tab, text="⚙️ Options Avancées")
        self.create_options_tab(options_tab)

    def create_main_tab(self, parent):
        """Crée l'onglet principal"""
        # En-tête
        header_frame = ttk.Frame(parent, padding="20")
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), columnspan=2)

        title_label = ttk.Label(header_frame, text="📸 PhotoFlow Master Pro", style='Title.TLabel')
        title_label.grid(row=0, column=0, sticky=tk.W)

        subtitle_label = ttk.Label(header_frame, text="Organisez vos projets photo professionnels - Version Avancée", style='Subtitle.TLabel')
        subtitle_label.grid(row=1, column=0, sticky=tk.W)

        # Séparateur
        ttk.Separator(parent, orient='horizontal').grid(row=1, column=0, sticky=(tk.W, tk.E), columnspan=2, pady=10)

        # Panneau gauche - Sources
        left_frame = ttk.LabelFrame(parent, text="Sources et Projets", padding="10")
        left_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)

        # Liste des sources
        self.sources_tree = ttk.Treeview(left_frame, columns=('Nom', 'Date', 'Fichiers'), show='headings', height=8)
        self.sources_tree.heading('Nom', text='Nom du Projet')
        self.sources_tree.heading('Date', text='Date')
        self.sources_tree.heading('Fichiers', text='Fichiers')
        self.sources_tree.column('Nom', width=200)
        self.sources_tree.column('Date', width=100)
        self.sources_tree.column('Fichiers', width=80)
        self.sources_tree.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # Scrollbar pour la liste
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.sources_tree.yview)
        scrollbar.grid(row=0, column=3, sticky=(tk.N, tk.S))
        self.sources_tree.configure(yscrollcommand=scrollbar.set)

        # Boutons pour gérer les sources
        btn_add_source = ttk.Button(left_frame, text="➕ Ajouter", command=self.add_source)
        btn_add_source.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=2, pady=5)

        btn_batch_add = ttk.Button(left_frame, text="📦 Mode Batch", command=self.batch_add_sources)
        btn_batch_add.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=2, pady=5)

        btn_remove_source = ttk.Button(left_frame, text="➖ Supprimer", command=self.remove_source)
        btn_remove_source.grid(row=1, column=2, sticky=(tk.W, tk.E), padx=2, pady=5)

        # Panneau droit - Configuration
        right_frame = ttk.LabelFrame(parent, text="Configuration", padding="10")
        right_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)

        # Sélection du disque de destination
        ttk.Label(right_frame, text="Disque de destination:", font=('Helvetica', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=5)

        disk_frame = ttk.Frame(right_frame)
        disk_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)

        self.drive_var = tk.StringVar()
        self.drive_combo = ttk.Combobox(disk_frame, textvariable=self.drive_var, state='readonly', width=25)
        self.drive_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_refresh_drives = ttk.Button(disk_frame, text="🔄", command=self.refresh_drives, width=3)
        btn_refresh_drives.pack(side=tk.LEFT, padx=5)

        # Espace disque disponible
        self.disk_space_label = ttk.Label(right_frame, text="", font=('Helvetica', 9))
        self.disk_space_label.grid(row=2, column=0, sticky=tk.W, pady=2)
        self.drive_combo.bind('<<ComboboxSelected>>', lambda e: self.update_disk_space())

        # Mode de copie rapide
        ttk.Label(right_frame, text="Mode d'opération:", font=('Helvetica', 10, 'bold')).grid(row=3, column=0, sticky=tk.W, pady=(10, 5))

        copy_modes = [
            ("📋 Copier", "copy"),
            ("✂️ Déplacer", "move"),
            ("🔗 Liens symboliques", "symlink"),
            ("🗜️ Compresser (ZIP)", "compress"),
        ]

        for i, (text, mode) in enumerate(copy_modes):
            ttk.Radiobutton(right_frame, text=text, variable=self.copy_mode, value=mode).grid(
                row=4+i, column=0, sticky=tk.W, padx=20
            )

        # Informations sur la structure
        info_frame = ttk.LabelFrame(right_frame, text="Structure créée", padding="10")
        info_frame.grid(row=8, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        structure_text = """📁 PROJETS_PHOTO/ANNÉE/DATE_NOM/
  ├── 01_PRE-PRODUCTION
  ├── 02_RAW (photos sources)
  ├── 03_SELECTS
  ├── 04_RETOUCHE
  ├── 05_VIDEO
  └── 06_ADMIN"""

        structure_label = ttk.Label(info_frame, text=structure_text, font=('Courier', 8), justify=tk.LEFT)
        structure_label.grid(row=0, column=0, sticky=tk.W)

        # Zone de logs
        log_frame = ttk.LabelFrame(parent, text="Journal d'activité", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=100, state='disabled',
                                                   bg='#ecf0f1', font=('Courier', 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Barre de progression avec détails
        progress_frame = ttk.Frame(parent)
        progress_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=5)

        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.pack(fill=tk.X, expand=True)

        self.progress_label = ttk.Label(progress_frame, text="", font=('Helvetica', 9))
        self.progress_label.pack(anchor=tk.W, pady=2)

        # Boutons principaux
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=5, column=0, columnspan=2, pady=15)

        self.btn_stats = ttk.Button(button_frame, text="📊 Analyser", command=self.show_statistics, style='Action.TButton')
        self.btn_stats.pack(side=tk.LEFT, padx=5)

        self.btn_process = ttk.Button(button_frame, text="🚀 LANCER L'ORGANISATION",
                                      command=self.start_processing, style='Action.TButton')
        self.btn_process.pack(side=tk.LEFT, padx=5)

        self.btn_cancel = ttk.Button(button_frame, text="⛔ ANNULER",
                                     command=self.cancel_operation, state='disabled')
        self.btn_cancel.pack(side=tk.LEFT, padx=5)

        # Configuration du redimensionnement
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(2, weight=1)
        parent.rowconfigure(3, weight=1)
        left_frame.columnconfigure(0, weight=1)
        left_frame.columnconfigure(1, weight=1)
        left_frame.columnconfigure(2, weight=1)
        left_frame.rowconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(8, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        # Charger les disques disponibles
        self.refresh_drives()

    def create_options_tab(self, parent):
        """Crée l'onglet des options avancées"""
        # Frame principale avec scrollbar
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Filtres de fichiers
        filter_frame = ttk.LabelFrame(scrollable_frame, text="🔍 Filtres de Types de Fichiers", padding="15")
        filter_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)

        ttk.Label(filter_frame, text="Sélectionnez les types de fichiers à inclure:", font=('Helvetica', 10, 'bold')).grid(
            row=0, column=0, columnspan=4, sticky=tk.W, pady=5
        )

        row, col = 1, 0
        for ext, var in self.file_filters.items():
            ttk.Checkbutton(filter_frame, text=ext, variable=var).grid(row=row, column=col, sticky=tk.W, padx=10)
            col += 1
            if col > 3:
                col = 0
                row += 1

        # Gestion des doublons
        duplicate_frame = ttk.LabelFrame(scrollable_frame, text="🔄 Gestion des Doublons", padding="15")
        duplicate_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)

        ttk.Label(duplicate_frame, text="Que faire en cas de fichier existant:", font=('Helvetica', 10, 'bold')).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )

        dup_strategies = [
            ("Renommer automatiquement (fichier_1, fichier_2, ...)", "rename"),
            ("Ignorer (ne pas copier)", "skip"),
            ("Remplacer (écraser l'existant)", "replace"),
        ]

        for i, (text, value) in enumerate(dup_strategies):
            ttk.Radiobutton(duplicate_frame, text=text, variable=self.duplicate_strategy, value=value).grid(
                row=i+1, column=0, sticky=tk.W, padx=20
            )

        # Renommage automatique
        rename_frame = ttk.LabelFrame(scrollable_frame, text="✏️ Renommage Automatique", padding="15")
        rename_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)

        ttk.Label(rename_frame, text="Pattern de renommage:", font=('Helvetica', 10, 'bold')).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )

        patterns = [
            ("{original}", "Nom original"),
            ("{date}_{original}", "Date_Nom"),
            ("{project}_{counter:04d}", "Projet_0001"),
            ("{date}_{project}_{counter:04d}", "Date_Projet_0001"),
        ]

        for i, (pattern, desc) in enumerate(patterns):
            ttk.Radiobutton(rename_frame, text=f"{desc} ({pattern})",
                          variable=self.rename_pattern, value=pattern).grid(
                row=i+1, column=0, sticky=tk.W, padx=20
            )

        # Options de performance
        perf_frame = ttk.LabelFrame(scrollable_frame, text="⚡ Performance et Vérification", padding="15")
        perf_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)

        ttk.Checkbutton(perf_frame, text="Utiliser le multi-threading (copie parallèle)",
                       variable=self.use_multithread).grid(row=0, column=0, sticky=tk.W, pady=5)

        thread_frame = ttk.Frame(perf_frame)
        thread_frame.grid(row=1, column=0, sticky=tk.W, padx=20)
        ttk.Label(thread_frame, text="Nombre de threads:").pack(side=tk.LEFT)
        ttk.Spinbox(thread_frame, from_=1, to=16, textvariable=self.max_threads, width=5).pack(side=tk.LEFT, padx=5)

        ttk.Checkbutton(perf_frame, text="Vérifier l'intégrité des fichiers (checksum MD5)",
                       variable=self.verify_integrity).grid(row=2, column=0, sticky=tk.W, pady=5)

        ttk.Checkbutton(perf_frame, text="Détecter les photos corrompues avant traitement",
                       variable=self.detect_corrupted).grid(row=3, column=0, sticky=tk.W, pady=5)

        ttk.Checkbutton(perf_frame, text="Confirmer avant d'écraser un projet existant",
                       variable=self.confirm_overwrite).grid(row=4, column=0, sticky=tk.W, pady=5)

        # Format de date
        date_frame = ttk.LabelFrame(scrollable_frame, text="📅 Format de Date", padding="15")
        date_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)

        ttk.Label(date_frame, text="Format de date pour la saisie manuelle:", font=('Helvetica', 10, 'bold')).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )

        for i, (fmt, desc) in enumerate(self.date_formats):
            ttk.Radiobutton(date_frame, text=f"{desc} (ex: {datetime.now().strftime(fmt)})",
                          variable=self.current_date_format, value=fmt).grid(
                row=i+1, column=0, sticky=tk.W, padx=20
            )

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def log(self, message, level='info'):
        """Ajoute un message au journal d'activité"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"

        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

        if level == 'info':
            self.logger.info(message)
        elif level == 'error':
            self.logger.error(message)
        elif level == 'warning':
            self.logger.warning(message)

    def refresh_drives(self):
        """Actualise la liste des disques disponibles"""
        partitions = psutil.disk_partitions()
        drives = [Path(part.mountpoint) for part in partitions if Path(part.mountpoint).exists()]
        self.drive_combo['values'] = [str(drive) for drive in drives]
        if drives:
            self.drive_combo.current(0)
            self.update_disk_space()
        self.log(f"🔄 {len(drives)} disque(s) détecté(s)")

    def update_disk_space(self):
        """Met à jour l'affichage de l'espace disque disponible"""
        if self.drive_var.get():
            try:
                usage = psutil.disk_usage(self.drive_var.get())
                free_gb = usage.free / (1024**3)
                total_gb = usage.total / (1024**3)
                percent = usage.percent
                self.disk_space_label.config(
                    text=f"💾 Espace: {free_gb:.1f} GB libre / {total_gb:.1f} GB total ({100-percent:.1f}% libre)"
                )
            except:
                self.disk_space_label.config(text="")

    def sanitize_filename(self, name: str) -> str:
        """Nettoie un nom de fichier pour éviter les conflits OS"""
        return re.sub(r'[<>:"/\\|?*]', '_', name)

    def format_size(self, size_bytes):
        """Formate une taille en octets en format lisible"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def get_file_count_and_size(self, path: Path):
        """Compte les fichiers et calcule la taille totale d'un dossier"""
        total_files = 0
        total_size = 0
        enabled_extensions = {ext.upper() for ext, var in self.file_filters.items() if var.get()}

        for file in path.rglob("*"):
            if file.is_file() and file.suffix.upper() in enabled_extensions:
                total_files += 1
                try:
                    total_size += file.stat().st_size
                except:
                    pass

        return total_files, total_size

    def batch_add_sources(self):
        """Mode batch - Détection automatique de plusieurs projets dans un dossier"""
        parent_path = filedialog.askdirectory(title="Sélectionnez le dossier parent contenant plusieurs projets")
        if not parent_path:
            return

        parent_path = Path(parent_path)

        # Rechercher les sous-dossiers
        subdirs = [d for d in parent_path.iterdir() if d.is_dir()]

        if not subdirs:
            messagebox.showinfo("Aucun projet", "Aucun sous-dossier trouvé dans ce répertoire.")
            return

        # Dialogue de sélection
        dialog = tk.Toplevel(self.root)
        dialog.title("Mode Batch - Sélection des Projets")
        dialog.geometry("600x400")
        dialog.transient(self.root)

        ttk.Label(dialog, text=f"Trouvé {len(subdirs)} dossier(s). Sélectionnez ceux à ajouter:",
                 font=('Helvetica', 10, 'bold')).pack(pady=10)

        # Liste avec checkboxes
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        selections = {}
        for i, subdir in enumerate(subdirs):
            var = tk.BooleanVar(value=True)
            selections[subdir] = var
            ttk.Checkbutton(scrollable_frame, text=f"📁 {subdir.name}", variable=var).pack(anchor=tk.W, pady=2)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def on_confirm():
            selected = [path for path, var in selections.items() if var.get()]
            if not selected:
                messagebox.showwarning("Aucune sélection", "Veuillez sélectionner au moins un dossier.")
                return

            # Ajouter chaque dossier sélectionné
            for subdir in selected:
                file_count, size = self.get_file_count_and_size(subdir)
                self.sources.append({
                    'path': subdir,
                    'name': self.sanitize_filename(subdir.name),
                    'date': "AUTO",
                    'file_count': file_count,
                    'size': size
                })
                self.sources_tree.insert('', tk.END, values=(subdir.name, "AUTO", file_count))

            self.log(f"📦 Mode batch: {len(selected)} projet(s) ajouté(s)")
            dialog.destroy()

        ttk.Button(dialog, text="✅ Confirmer", command=on_confirm).pack(pady=10)

    def add_source(self):
        """Ajoute une nouvelle source avec dialogue"""
        if len(self.sources) >= 10:
            messagebox.showwarning("Limite atteinte", "Vous pouvez ajouter jusqu'à 10 sources maximum.")
            return

        # Sélection du dossier
        source_path = filedialog.askdirectory(title="Sélectionnez le dossier source")
        if not source_path:
            return

        source_path = Path(source_path)

        # Compter les fichiers
        self.log(f"🔍 Analyse du dossier {source_path.name}...")
        file_count, size = self.get_file_count_and_size(source_path)

        # Dialogue pour le nom du projet
        dialog = tk.Toplevel(self.root)
        dialog.title("Nouveau Projet")
        dialog.geometry("500x250")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=f"Dossier: {source_path.name}",
                 font=('Helvetica', 10, 'bold')).pack(pady=10)

        ttk.Label(dialog, text=f"📊 {file_count} fichiers ({self.format_size(size)})",
                 font=('Helvetica', 9)).pack(pady=5)

        ttk.Label(dialog, text="Nom du projet:").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.pack(pady=5)
        name_entry.insert(0, source_path.name)
        name_entry.focus()

        ttk.Label(dialog, text=f"Date ({self.current_date_format.get()}) - laisser vide pour détection auto:").pack(pady=5)
        date_entry = ttk.Entry(dialog, width=40)
        date_entry.pack(pady=5)

        def on_ok():
            project_name = name_entry.get().strip()
            date_str = date_entry.get().strip()

            if not project_name:
                messagebox.showerror("Erreur", "Le nom du projet ne peut pas être vide.")
                return

            # Validation de la date si fournie
            if date_str:
                try:
                    date_obj = datetime.strptime(date_str, self.current_date_format.get())
                    date_iso = date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Erreur", f"Format de date invalide. Utilisez {self.current_date_format.get()}.")
                    return
            else:
                date_iso = "AUTO"

            # Ajouter à la liste
            self.sources.append({
                'path': source_path,
                'name': self.sanitize_filename(project_name),
                'date': date_iso,
                'file_count': file_count,
                'size': size
            })

            # Ajouter à la vue
            self.sources_tree.insert('', tk.END, values=(project_name, date_iso, file_count))
            self.log(f"➕ Source ajoutée: {project_name} ({file_count} fichiers)")
            dialog.destroy()

        ttk.Button(dialog, text="✅ Ajouter", command=on_ok).pack(pady=10)
        dialog.bind('<Return>', lambda e: on_ok())

    def remove_source(self):
        """Supprime la source sélectionnée"""
        selection = self.sources_tree.selection()
        if not selection:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner une source à supprimer.")
            return

        item = selection[0]
        index = self.sources_tree.index(item)

        self.sources_tree.delete(item)
        removed = self.sources.pop(index)
        self.log(f"➖ Source supprimée: {removed['name']}")

    def is_image_corrupted(self, image_path: Path) -> bool:
        """Vérifie si une image est corrompue"""
        try:
            with Image.open(image_path) as img:
                img.verify()
            return False
        except:
            return True

    def calculate_checksum(self, file_path: Path, algorithm='md5') -> str:
        """Calcule le checksum d'un fichier"""
        hash_func = hashlib.md5() if algorithm == 'md5' else hashlib.sha256()

        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except:
            return None

    def extract_date_taken(self, image_path: Path) -> datetime:
        """Extrait la date de prise de vue des métadonnées EXIF"""
        try:
            with Image.open(image_path) as img:
                exif_data = img.getexif()
                if exif_data:
                    for tag, value in exif_data.items():
                        if TAGS.get(tag) == "DateTimeOriginal":
                            return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
        except Exception as e:
            self.logger.error(f"Erreur EXIF pour {image_path}: {e}")
        return None

    def find_date_in_source(self, source_path: Path) -> datetime:
        """Recherche la date la plus ancienne dans les métadonnées EXIF des images"""
        earliest_date = None
        enabled_extensions = {ext.upper() for ext, var in self.file_filters.items() if var.get()}

        for file in source_path.rglob("*"):
            if file.suffix.upper() in enabled_extensions:
                date_taken = self.extract_date_taken(file)
                if date_taken:
                    if earliest_date is None or date_taken < earliest_date:
                        earliest_date = date_taken
                        self.log(f"✅ Date trouvée: {date_taken.strftime('%d-%m-%Y')} dans {file.name}")
        return earliest_date

    def show_statistics(self):
        """Affiche les statistiques avant traitement"""
        if not self.sources:
            messagebox.showwarning("Aucune source", "Ajoutez au moins une source pour voir les statistiques.")
            return

        # Calculer les statistiques
        total_files = 0
        total_size = 0
        file_types = defaultdict(int)
        corrupted_files = []

        # Dialogue de progression
        progress_dialog = tk.Toplevel(self.root)
        progress_dialog.title("Analyse en cours...")
        progress_dialog.geometry("500x150")
        progress_dialog.transient(self.root)
        progress_dialog.grab_set()

        ttk.Label(progress_dialog, text="🔍 Analyse des fichiers...",
                 font=('Helvetica', 11, 'bold')).pack(pady=15)

        progress_bar = ttk.Progressbar(progress_dialog, mode='indeterminate')
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        progress_bar.start()

        status_label = ttk.Label(progress_dialog, text="")
        status_label.pack(pady=10)

        def analyze():
            nonlocal total_files, total_size, file_types, corrupted_files
            enabled_extensions = {ext.upper() for ext, var in self.file_filters.items() if var.get()}

            for source in self.sources:
                status_label.config(text=f"Analyse: {source['name']}")
                for file in source['path'].rglob("*"):
                    if file.is_file() and file.suffix.upper() in enabled_extensions:
                        total_files += 1
                        try:
                            size = file.stat().st_size
                            total_size += size
                            file_types[file.suffix.upper()] += 1

                            # Vérifier corruption si activé
                            if self.detect_corrupted.get() and file.suffix.upper() in {'.JPG', '.JPEG', '.PNG', '.TIFF'}:
                                if self.is_image_corrupted(file):
                                    corrupted_files.append(file)
                        except:
                            pass

            progress_dialog.destroy()
            self.display_statistics(total_files, total_size, file_types, corrupted_files)

        threading.Thread(target=analyze, daemon=True).start()

    def display_statistics(self, total_files, total_size, file_types, corrupted_files):
        """Affiche le dialogue de statistiques"""
        # Vérifier l'espace disque
        if self.drive_var.get():
            usage = psutil.disk_usage(self.drive_var.get())
            free_space = usage.free
            enough_space = free_space > total_size * 1.1  # 10% de marge
        else:
            enough_space = True

        # Dialogue de statistiques
        stats_dialog = tk.Toplevel(self.root)
        stats_dialog.title("📊 Statistiques du Traitement")
        stats_dialog.geometry("600x550")
        stats_dialog.transient(self.root)

        # En-tête
        header = ttk.Label(stats_dialog, text="📊 Analyse Complète", font=('Helvetica', 14, 'bold'))
        header.pack(pady=15)

        # Frame principal
        main_frame = ttk.Frame(stats_dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Statistiques générales
        general_frame = ttk.LabelFrame(main_frame, text="📈 Vue d'ensemble", padding="10")
        general_frame.pack(fill=tk.X, pady=5)

        ttk.Label(general_frame, text=f"Nombre de projets:", font=('Helvetica', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=3)
        ttk.Label(general_frame, text=f"{len(self.sources)}").grid(row=0, column=1, sticky=tk.W, padx=20)

        ttk.Label(general_frame, text=f"Fichiers à traiter:", font=('Helvetica', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=3)
        ttk.Label(general_frame, text=f"{total_files}").grid(row=1, column=1, sticky=tk.W, padx=20)

        ttk.Label(general_frame, text=f"Taille totale:", font=('Helvetica', 10, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=3)
        ttk.Label(general_frame, text=f"{self.format_size(total_size)}").grid(row=2, column=1, sticky=tk.W, padx=20)

        # Répartition par type
        types_frame = ttk.LabelFrame(main_frame, text="📂 Répartition par Type", padding="10")
        types_frame.pack(fill=tk.X, pady=5)

        sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
        for i, (ext, count) in enumerate(sorted_types[:8]):  # Top 8
            percentage = (count / total_files * 100) if total_files > 0 else 0
            ttk.Label(types_frame, text=f"{ext}:").grid(row=i, column=0, sticky=tk.W, pady=2)
            ttk.Label(types_frame, text=f"{count} fichiers ({percentage:.1f}%)").grid(row=i, column=1, sticky=tk.W, padx=20)

        # Espace disque
        disk_frame = ttk.LabelFrame(main_frame, text="💾 Espace Disque", padding="10")
        disk_frame.pack(fill=tk.X, pady=5)

        if self.drive_var.get():
            usage = psutil.disk_usage(self.drive_var.get())
            ttk.Label(disk_frame, text=f"Espace requis:", font=('Helvetica', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=3)

            # Ajuster selon le mode
            required_space = total_size
            if self.copy_mode.get() == "compress":
                required_space = total_size * 0.7  # Estimation compression
            elif self.copy_mode.get() == "symlink":
                required_space = total_files * 1024  # Très petit pour les liens

            ttk.Label(disk_frame, text=f"{self.format_size(required_space)}").grid(row=0, column=1, sticky=tk.W, padx=20)

            ttk.Label(disk_frame, text=f"Espace disponible:", font=('Helvetica', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=3)
            ttk.Label(disk_frame, text=f"{self.format_size(usage.free)}").grid(row=1, column=1, sticky=tk.W, padx=20)

            status_text = "✅ Espace suffisant" if enough_space else "⚠️ Espace insuffisant!"
            status_color = "green" if enough_space else "red"
            status_label = ttk.Label(disk_frame, text=status_text, foreground=status_color, font=('Helvetica', 10, 'bold'))
            status_label.grid(row=2, column=0, columnspan=2, pady=5)

        # Photos corrompues
        if corrupted_files:
            corrupt_frame = ttk.LabelFrame(main_frame, text="⚠️ Fichiers Corrompus Détectés", padding="10")
            corrupt_frame.pack(fill=tk.X, pady=5)

            ttk.Label(corrupt_frame, text=f"{len(corrupted_files)} fichier(s) corrompu(s) trouvé(s)",
                     foreground="orange", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W)

            if len(corrupted_files) <= 5:
                for f in corrupted_files:
                    ttk.Label(corrupt_frame, text=f"  • {f.name}", font=('Courier', 8)).pack(anchor=tk.W)
            else:
                ttk.Label(corrupt_frame, text=f"  (voir les logs pour la liste complète)",
                         font=('Courier', 8)).pack(anchor=tk.W)

        # Boutons
        button_frame = ttk.Frame(stats_dialog)
        button_frame.pack(pady=15)

        ttk.Button(button_frame, text="✅ OK", command=stats_dialog.destroy).pack(side=tk.LEFT, padx=5)

        if not enough_space:
            ttk.Button(button_frame, text="⚠️ Continuer quand même",
                      command=lambda: [stats_dialog.destroy(), self.start_processing()]).pack(side=tk.LEFT, padx=5)

    def apply_rename_pattern(self, file_path: Path, project_name: str, counter: int, date: str) -> str:
        """Applique le pattern de renommage"""
        pattern = self.rename_pattern.get()

        replacements = {
            '{original}': file_path.stem,
            '{project}': project_name,
            '{counter:04d}': f"{counter:04d}",
            '{date}': date,
            '{ext}': file_path.suffix,
        }

        new_name = pattern
        for key, value in replacements.items():
            new_name = new_name.replace(key, value)

        return new_name + file_path.suffix

    def handle_duplicate(self, destination: Path) -> Path:
        """Gère les fichiers en double selon la stratégie choisie"""
        strategy = self.duplicate_strategy.get()

        if strategy == "skip":
            return None
        elif strategy == "replace":
            return destination
        elif strategy == "rename":
            counter = 1
            stem = destination.stem
            suffix = destination.suffix
            new_dest = destination
            while new_dest.exists():
                new_dest = destination.parent / f"{stem}_{counter}{suffix}"
                counter += 1
            return new_dest

        return destination

    def copy_file(self, source: Path, destination: Path, mode: str):
        """Copie un fichier selon le mode choisi"""
        if self.cancel_flag:
            return False

        # Gérer les doublons
        if destination.exists():
            destination = self.handle_duplicate(destination)
            if destination is None:
                self.log(f"⏭️ Ignoré (doublon): {source.name}")
                return False

        try:
            if mode == "copy":
                shutil.copy2(source, destination)
            elif mode == "move":
                shutil.move(str(source), str(destination))
            elif mode == "symlink":
                os.symlink(source, destination)
            elif mode == "compress":
                # Compression dans le mode organize_files
                pass

            # Vérification d'intégrité
            if self.verify_integrity.get() and mode in ["copy", "move"]:
                source_hash = self.calculate_checksum(source)
                dest_hash = self.calculate_checksum(destination)
                if source_hash != dest_hash:
                    self.log(f"❌ Erreur d'intégrité: {source.name}", 'error')
                    return False

            return True
        except Exception as e:
            self.log(f"❌ Erreur copie {source.name}: {e}", 'error')
            return False

    def create_project_structure(self, base_path: Path, project_name: str) -> Path:
        """Crée la structure de dossiers du projet"""
        project_path = base_path / project_name

        # Vérifier si le projet existe déjà
        if project_path.exists() and self.confirm_overwrite.get():
            response = messagebox.askyesno(
                "Projet existant",
                f"Le projet '{project_name}' existe déjà.\n\nVoulez-vous continuer et fusionner les fichiers?",
                icon='warning'
            )
            if not response:
                raise Exception(f"Opération annulée: le projet {project_name} existe déjà")

        structure = {
            "01_PRE-PRODUCTION": ["Moodboard", "References", "Brief"],
            "02_RAW": [],
            "03_SELECTS": [],
            "04_RETOUCHE": ["PSD", "FINALS"],
            "05_VIDEO": ["RUSH", "FINALS"],
            "06_ADMIN": ["Factures", "Contrats"],
        }

        for folder, subfolders in structure.items():
            folder_path = project_path / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            for subfolder in subfolders:
                (folder_path / subfolder).mkdir(parents=True, exist_ok=True)

        self.log(f"✅ Structure créée: {project_path}")
        return project_path

    def organize_files(self, source_path: Path, project_path: Path, project_name: str, date_str: str):
        """Organise les fichiers dans le dossier 02_RAW"""
        if self.cancel_flag:
            return

        raw_folder = project_path / "02_RAW"
        raw_folder.mkdir(parents=True, exist_ok=True)

        # Récupérer les fichiers filtrés
        enabled_extensions = {ext.upper() for ext, var in self.file_filters.items() if var.get()}
        files = [f for f in source_path.rglob("*") if f.is_file() and f.suffix.upper() in enabled_extensions]

        total = len(files)
        if total == 0:
            self.log(f"⚠️ Aucun fichier à traiter pour {project_name}", 'warning')
            return

        # Mode compression
        if self.copy_mode.get() == "compress":
            zip_path = raw_folder / f"{project_name}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for i, file in enumerate(files):
                    if self.cancel_flag:
                        break
                    zipf.write(file, file.name)
                    self.update_progress(i + 1, total)
            self.log(f"📦 Archive créée: {zip_path.name}")
            return

        # Multi-threading ou séquentiel
        if self.use_multithread.get() and total > 10:
            self.organize_files_multithread(files, raw_folder, project_name, date_str, total)
        else:
            self.organize_files_sequential(files, raw_folder, project_name, date_str, total)

    def organize_files_sequential(self, files, raw_folder, project_name, date_str, total):
        """Organisation séquentielle des fichiers"""
        for i, file in enumerate(files):
            if self.cancel_flag:
                break

            # Renommage
            if self.rename_pattern.get() != "{original}":
                new_name = self.apply_rename_pattern(file, project_name, i + 1, date_str)
                destination = raw_folder / new_name
            else:
                destination = raw_folder / file.name

            # Copie
            if self.copy_file(file, destination, self.copy_mode.get()):
                self.stats['processed_files'] += 1
                try:
                    self.stats['processed_size'] += file.stat().st_size
                except:
                    pass

            self.update_progress(i + 1, total)

    def organize_files_multithread(self, files, raw_folder, project_name, date_str, total):
        """Organisation multi-thread des fichiers"""
        completed = 0

        def process_file(args):
            i, file = args
            if self.cancel_flag:
                return False

            if self.rename_pattern.get() != "{original}":
                new_name = self.apply_rename_pattern(file, project_name, i + 1, date_str)
                destination = raw_folder / new_name
            else:
                destination = raw_folder / file.name

            return self.copy_file(file, destination, self.copy_mode.get())

        with ThreadPoolExecutor(max_workers=self.max_threads.get()) as executor:
            futures = {executor.submit(process_file, (i, f)): f for i, f in enumerate(files)}

            for future in as_completed(futures):
                if self.cancel_flag:
                    executor.shutdown(wait=False)
                    break

                if future.result():
                    file = futures[future]
                    self.stats['processed_files'] += 1
                    try:
                        self.stats['processed_size'] += file.stat().st_size
                    except:
                        pass

                completed += 1
                self.update_progress(completed, total)

    def update_progress(self, current, total):
        """Met à jour la barre de progression avec détails"""
        if total == 0:
            return

        percentage = (current / total) * 100
        self.progress['value'] = percentage

        # Calcul du temps estimé
        if self.stats['start_time']:
            elapsed = time() - self.stats['start_time']
            if current > 0:
                rate = current / elapsed
                remaining = (total - current) / rate if rate > 0 else 0

                # Formatage du temps
                elapsed_str = f"{int(elapsed//60)}m {int(elapsed%60)}s"
                remaining_str = f"{int(remaining//60)}m {int(remaining%60)}s"

                # Taille traitée
                size_str = self.format_size(self.stats['processed_size'])
                total_size_str = self.format_size(self.stats['total_size'])

                text = f"{current}/{total} fichiers ({percentage:.1f}%) • {size_str}/{total_size_str} • "
                text += f"⏱️ {elapsed_str} • Reste: {remaining_str}"
            else:
                text = f"{current}/{total} fichiers ({percentage:.1f}%)"
        else:
            text = f"{current}/{total} fichiers ({percentage:.1f}%)"

        self.progress_label.config(text=text)
        self.root.update_idletasks()

    def process_sources(self):
        """Traite toutes les sources (appelé dans un thread)"""
        try:
            self.cancel_flag = False
            self.stats['start_time'] = time()
            self.stats['processed_files'] = 0
            self.stats['processed_size'] = 0

            # Calculer taille totale
            self.stats['total_size'] = sum(s.get('size', 0) for s in self.sources)

            self.log("🚀 Début du traitement...")

            if not self.sources:
                messagebox.showerror("Erreur", "Aucune source ajoutée.")
                return

            if not self.drive_var.get():
                messagebox.showerror("Erreur", "Aucun disque de destination sélectionné.")
                return

            selected_drive = Path(self.drive_var.get())

            # Détecter les dates automatiques
            for source in self.sources:
                if self.cancel_flag:
                    break

                if source['date'] == "AUTO":
                    self.log(f"🔍 Détection date pour {source['name']}...")
                    date_obj = self.find_date_in_source(source['path'])
                    if date_obj:
                        source['date'] = date_obj.strftime("%Y-%m-%d")
                        self.log(f"✅ Date détectée: {date_obj.strftime('%d-%m-%Y')}")
                    else:
                        self.log(f"⚠️ Aucune date trouvée pour {source['name']}", 'warning')
                        self.root.after(0, lambda s=source: self.ask_manual_date(s))
                        return

            # Créer les structures et organiser
            for source in self.sources:
                if self.cancel_flag:
                    self.log("⛔ Opération annulée par l'utilisateur", 'warning')
                    break

                self.log(f"📂 Traitement de {source['name']}...")

                year = source['date'].split("-")[0]
                base_path = selected_drive / "PROJETS_PHOTO" / year
                base_path.mkdir(parents=True, exist_ok=True)

                project_folder_name = f"{source['date']}_{source['name']}"

                try:
                    project_path = self.create_project_structure(base_path, project_folder_name)
                    self.organize_files(source['path'], project_path, source['name'], source['date'])
                except Exception as e:
                    self.log(f"❌ Erreur pour {source['name']}: {e}", 'error')
                    continue

            if not self.cancel_flag:
                self.log("✨ Organisation terminée avec succès!")
                messagebox.showinfo("Succès", "Tous les projets ont été organisés avec succès!")
            else:
                messagebox.showwarning("Annulé", "L'opération a été annulée.")

        except Exception as e:
            error_msg = f"Erreur lors du traitement: {e}"
            self.log(f"❌ {error_msg}", 'error')
            messagebox.showerror("Erreur", error_msg)
        finally:
            self.root.after(0, self.stop_progress)

    def ask_manual_date(self, source):
        """Demande une date manuelle pour une source"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Date Manuelle Requise")
        dialog.geometry("450x180")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=f"Aucune date trouvée pour: {source['name']}",
                 font=('Helvetica', 10, 'bold')).pack(pady=10)

        current_fmt = self.current_date_format.get()
        fmt_display = next(desc for fmt, desc in self.date_formats if fmt == current_fmt)

        ttk.Label(dialog, text=f"Veuillez entrer la date ({fmt_display}):").pack(pady=5)
        date_entry = ttk.Entry(dialog, width=30)
        date_entry.pack(pady=5)
        date_entry.focus()

        ttk.Label(dialog, text=f"Exemple: {datetime.now().strftime(current_fmt)}",
                 font=('Helvetica', 8, 'italic')).pack(pady=2)

        def on_ok():
            date_str = date_entry.get().strip()
            try:
                date_obj = datetime.strptime(date_str, current_fmt)
                source['date'] = date_obj.strftime("%Y-%m-%d")
                self.log(f"✅ Date manuelle: {date_str} pour {source['name']}")
                dialog.destroy()
                threading.Thread(target=self.process_sources, daemon=True).start()
            except ValueError:
                messagebox.showerror("Erreur", f"Format de date invalide. Utilisez {fmt_display}.")

        ttk.Button(dialog, text="✅ Valider", command=on_ok).pack(pady=10)
        dialog.bind('<Return>', lambda e: on_ok())

    def start_processing(self):
        """Lance le traitement dans un thread séparé"""
        self.btn_process.config(state='disabled')
        self.btn_cancel.config(state='normal')
        self.progress['mode'] = 'determinate'
        self.progress['value'] = 0

        threading.Thread(target=self.process_sources, daemon=True).start()

    def cancel_operation(self):
        """Annule l'opération en cours"""
        if messagebox.askyesno("Confirmer", "Voulez-vous vraiment annuler l'opération en cours?"):
            self.cancel_flag = True
            self.log("⛔ Annulation en cours...", 'warning')

    def stop_progress(self):
        """Arrête la barre de progression"""
        self.progress['value'] = 0
        self.progress_label.config(text="")
        self.btn_process.config(state='normal')
        self.btn_cancel.config(state='disabled')
        self.cancel_flag = False


def main():
    """Point d'entrée principal"""
    root = tk.Tk()
    app = PhotoProManagerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
