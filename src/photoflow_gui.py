#!/usr/bin/env python3
"""
PhotoFlow Master - Interface Graphique
Gestionnaire professionnel de projets photo avec interface GUI
"""

from pathlib import Path
from datetime import datetime
import re
import shutil
import logging
import psutil
import threading
from PIL import Image
from PIL.ExifTags import TAGS
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext


class PhotoProManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📸 PhotoFlow Master - Gestionnaire de Projets Photo")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # Variables
        self.sources = []  # Liste de dictionnaires: {'path': Path, 'name': str, 'date': str}
        self.selected_drive = None

        # Configuration du logging
        self.setup_logging()

        # Configuration du style
        self.setup_style()

        # Création de l'interface
        self.create_widgets()

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
        style.configure('Success.TButton', font=('Helvetica', 12, 'bold'), background='#27ae60', foreground='white')

    def create_widgets(self):
        """Crée tous les widgets de l'interface"""
        # En-tête
        header_frame = ttk.Frame(self.root, padding="20")
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), columnspan=2)

        title_label = ttk.Label(header_frame, text="📸 PhotoFlow Master", style='Title.TLabel')
        title_label.grid(row=0, column=0, sticky=tk.W)

        subtitle_label = ttk.Label(header_frame, text="Organisez vos projets photo professionnels", style='Subtitle.TLabel')
        subtitle_label.grid(row=1, column=0, sticky=tk.W)

        # Séparateur
        ttk.Separator(self.root, orient='horizontal').grid(row=1, column=0, sticky=(tk.W, tk.E), columnspan=2, pady=10)

        # Panneau gauche - Sources
        left_frame = ttk.LabelFrame(self.root, text="Sources et Projets", padding="10")
        left_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)

        # Liste des sources
        self.sources_tree = ttk.Treeview(left_frame, columns=('Nom', 'Date'), show='headings', height=8)
        self.sources_tree.heading('Nom', text='Nom du Projet')
        self.sources_tree.heading('Date', text='Date')
        self.sources_tree.column('Nom', width=200)
        self.sources_tree.column('Date', width=100)
        self.sources_tree.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # Scrollbar pour la liste
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.sources_tree.yview)
        scrollbar.grid(row=0, column=2, sticky=(tk.N, tk.S))
        self.sources_tree.configure(yscrollcommand=scrollbar.set)

        # Boutons pour gérer les sources
        btn_add_source = ttk.Button(left_frame, text="➕ Ajouter une Source", command=self.add_source)
        btn_add_source.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=2, pady=5)

        btn_remove_source = ttk.Button(left_frame, text="➖ Supprimer", command=self.remove_source)
        btn_remove_source.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=2, pady=5)

        # Panneau droit - Configuration
        right_frame = ttk.LabelFrame(self.root, text="Configuration", padding="10")
        right_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)

        # Sélection du disque de destination
        ttk.Label(right_frame, text="Disque de destination:", font=('Helvetica', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=5)

        self.drive_var = tk.StringVar()
        self.drive_combo = ttk.Combobox(right_frame, textvariable=self.drive_var, state='readonly', width=30)
        self.drive_combo.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)

        btn_refresh_drives = ttk.Button(right_frame, text="🔄 Actualiser", command=self.refresh_drives)
        btn_refresh_drives.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)

        # Informations sur la structure
        info_frame = ttk.LabelFrame(right_frame, text="Structure créée", padding="10")
        info_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        structure_text = """📁 PROJETS_PHOTO/ANNÉE/DATE_NOM/
  ├── 01_PRE-PRODUCTION
  │   ├── Moodboard
  │   ├── References
  │   └── Brief
  ├── 02_RAW (photos sources)
  ├── 03_SELECTS
  ├── 04_RETOUCHE
  │   ├── PSD
  │   └── FINALS
  ├── 05_VIDEO
  │   ├── RUSH
  │   └── FINALS
  └── 06_ADMIN
      ├── Factures
      └── Contrats"""

        structure_label = ttk.Label(info_frame, text=structure_text, font=('Courier', 8), justify=tk.LEFT)
        structure_label.grid(row=0, column=0, sticky=tk.W)

        # Zone de logs
        log_frame = ttk.LabelFrame(self.root, text="Journal d'activité", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=80, state='disabled',
                                                   bg='#ecf0f1', font=('Courier', 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Barre de progression
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=5)

        # Bouton principal
        self.btn_process = ttk.Button(self.root, text="🚀 LANCER L'ORGANISATION",
                                      command=self.start_processing, style='Action.TButton')
        self.btn_process.grid(row=5, column=0, columnspan=2, pady=20)

        # Configuration du redimensionnement
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=1)
        self.root.rowconfigure(3, weight=1)
        left_frame.columnconfigure(0, weight=1)
        left_frame.columnconfigure(1, weight=1)
        left_frame.rowconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        # Charger les disques disponibles
        self.refresh_drives()

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
        self.log(f"🔄 {len(drives)} disque(s) détecté(s)")

    def sanitize_filename(self, name: str) -> str:
        """Nettoie un nom de fichier pour éviter les conflits OS"""
        return re.sub(r'[<>:"/\\|?*]', '_', name)

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

        # Dialogue pour le nom du projet
        dialog = tk.Toplevel(self.root)
        dialog.title("Nouveau Projet")
        dialog.geometry("450x200")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=f"Dossier source: {source_path.name}",
                 font=('Helvetica', 10, 'bold')).pack(pady=10)

        ttk.Label(dialog, text="Nom du projet:").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.pack(pady=5)
        name_entry.insert(0, source_path.name)
        name_entry.focus()

        ttk.Label(dialog, text="Date (JJ-MM-AAAA) - laisser vide pour détection auto:").pack(pady=5)
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
                    date_obj = datetime.strptime(date_str, "%d-%m-%Y")
                    date_iso = date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Erreur", "Format de date invalide. Utilisez JJ-MM-AAAA.")
                    return
            else:
                date_iso = "AUTO"

            # Ajouter à la liste
            self.sources.append({
                'path': source_path,
                'name': self.sanitize_filename(project_name),
                'date': date_iso
            })

            # Ajouter à la vue
            self.sources_tree.insert('', tk.END, values=(project_name, date_iso))
            self.log(f"➕ Source ajoutée: {project_name} ({source_path})")
            dialog.destroy()

        ttk.Button(dialog, text="✅ Ajouter", command=on_ok).pack(pady=10)

        # Bind Enter key
        dialog.bind('<Return>', lambda e: on_ok())

    def remove_source(self):
        """Supprime la source sélectionnée"""
        selection = self.sources_tree.selection()
        if not selection:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner une source à supprimer.")
            return

        # Obtenir l'index
        item = selection[0]
        index = self.sources_tree.index(item)

        # Supprimer
        self.sources_tree.delete(item)
        removed = self.sources.pop(index)
        self.log(f"➖ Source supprimée: {removed['name']}")

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
        supported_formats = {".ARW", ".CR2", ".NEF", ".RAF", ".DNG", ".JPG", ".JPEG", ".TIFF"}

        for file in source_path.rglob("*"):
            if file.suffix.upper() in supported_formats:
                date_taken = self.extract_date_taken(file)
                if date_taken:
                    if earliest_date is None or date_taken < earliest_date:
                        earliest_date = date_taken
                        self.log(f"✅ Date trouvée: {date_taken.strftime('%d-%m-%Y')} dans {file.name}")
        return earliest_date

    def create_project_structure(self, base_path: Path, project_name: str) -> Path:
        """Crée la structure de dossiers du projet"""
        project_path = base_path / project_name

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

    def organize_files(self, source_path: Path, project_path: Path):
        """Organise les fichiers dans le dossier 02_RAW"""
        raw_folder = project_path / "02_RAW"
        raw_folder.mkdir(parents=True, exist_ok=True)

        files = list(source_path.rglob("*"))
        file_count = sum(1 for f in files if f.is_file())
        copied = 0

        for file in files:
            if file.is_file():
                destination = raw_folder / file.name

                # Gérer les collisions de noms
                if destination.exists():
                    counter = 1
                    stem = file.stem
                    suffix = file.suffix
                    while destination.exists():
                        destination = raw_folder / f"{stem}_{counter}{suffix}"
                        counter += 1
                    self.log(f"⚠️ Collision: {file.name} → {destination.name}", 'warning')

                try:
                    shutil.copy2(file, destination)
                    copied += 1
                    self.logger.info(f"Copié: {file} → {destination}")
                except Exception as e:
                    self.log(f"❌ Erreur copie {file.name}: {e}", 'error')

        self.log(f"📦 {copied}/{file_count} fichiers copiés depuis {source_path.name}")

    def process_sources(self):
        """Traite toutes les sources (appelé dans un thread)"""
        try:
            self.log("🚀 Début du traitement...")

            # Vérifier qu'il y a des sources
            if not self.sources:
                messagebox.showerror("Erreur", "Aucune source ajoutée.")
                return

            # Vérifier le disque sélectionné
            if not self.drive_var.get():
                messagebox.showerror("Erreur", "Aucun disque de destination sélectionné.")
                return

            selected_drive = Path(self.drive_var.get())

            # Détecter les dates automatiques
            for source in self.sources:
                if source['date'] == "AUTO":
                    self.log(f"🔍 Détection date pour {source['name']}...")
                    date_obj = self.find_date_in_source(source['path'])
                    if date_obj:
                        source['date'] = date_obj.strftime("%Y-%m-%d")
                        self.log(f"✅ Date détectée: {date_obj.strftime('%d-%m-%Y')}")
                    else:
                        # Demander manuellement
                        self.log(f"⚠️ Aucune date trouvée pour {source['name']}", 'warning')
                        self.root.after(0, lambda s=source: self.ask_manual_date(s))
                        return  # Attendre la saisie manuelle

            # Créer les structures et organiser
            for source in self.sources:
                self.log(f"📂 Traitement de {source['name']}...")

                # Créer le chemin de base
                year = source['date'].split("-")[0]
                base_path = selected_drive / "PROJETS_PHOTO" / year
                base_path.mkdir(parents=True, exist_ok=True)

                # Nom du dossier projet
                project_folder_name = f"{source['date']}_{source['name']}"

                # Créer la structure
                project_path = self.create_project_structure(base_path, project_folder_name)

                # Organiser les fichiers
                self.organize_files(source['path'], project_path)

            self.log("✨ Organisation terminée avec succès!")
            messagebox.showinfo("Succès", "Tous les projets ont été organisés avec succès!")

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
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=f"Aucune date trouvée pour: {source['name']}",
                 font=('Helvetica', 10, 'bold')).pack(pady=10)

        ttk.Label(dialog, text="Veuillez entrer la date (JJ-MM-AAAA):").pack(pady=5)
        date_entry = ttk.Entry(dialog, width=30)
        date_entry.pack(pady=5)
        date_entry.focus()

        def on_ok():
            date_str = date_entry.get().strip()
            try:
                date_obj = datetime.strptime(date_str, "%d-%m-%Y")
                source['date'] = date_obj.strftime("%Y-%m-%d")
                self.log(f"✅ Date manuelle: {date_str} pour {source['name']}")
                dialog.destroy()
                # Relancer le traitement
                threading.Thread(target=self.process_sources, daemon=True).start()
            except ValueError:
                messagebox.showerror("Erreur", "Format de date invalide. Utilisez JJ-MM-AAAA.")

        ttk.Button(dialog, text="✅ Valider", command=on_ok).pack(pady=10)
        dialog.bind('<Return>', lambda e: on_ok())

    def start_processing(self):
        """Lance le traitement dans un thread séparé"""
        self.btn_process.config(state='disabled')
        self.progress.start()

        # Lancer le traitement dans un thread
        threading.Thread(target=self.process_sources, daemon=True).start()

    def stop_progress(self):
        """Arrête la barre de progression"""
        self.progress.stop()
        self.btn_process.config(state='normal')


def main():
    """Point d'entrée principal"""
    root = tk.Tk()
    app = PhotoProManagerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
