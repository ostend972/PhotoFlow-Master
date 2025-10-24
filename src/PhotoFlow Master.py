from pathlib import Path
from datetime import datetime
import re
import shutil
import logging
import psutil
from PIL import Image
from PIL.ExifTags import TAGS
from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.panel import Panel
from rich.progress import track


class PhotoProManager:
    def __init__(self):
        self.console = Console()
        self.setup_logging()

    def setup_logging(self):
        log_dir = Path.home() / "Documents" / "PhotoProManager" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"manager_{datetime.now().strftime('%Y%m%d')}.log"
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger()

    def sanitize_filename(self, name: str) -> str:
        """Sanitize filename to avoid OS conflicts."""
        return re.sub(r'[<>:"/\\|?*]', '_', name)

    def extract_date_taken(self, image_path: Path) -> datetime:
        """Extract the shooting date from an image's EXIF metadata."""
        try:
            with Image.open(image_path) as img:
                exif_data = img.getexif()
                if exif_data:
                    for tag, value in exif_data.items():
                        if TAGS.get(tag) == "DateTimeOriginal":
                            return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
        except Exception as e:
            self.logger.error(f"Erreur lors de l'extraction EXIF pour {image_path}: {e}")
        return None

    def find_date_in_source(self, source_path: Path) -> datetime:
        """Search for the earliest date in the EXIF metadata of images in a single source path."""
        earliest_date = None
        for file in source_path.rglob("*"):
            if file.suffix.upper() in {".ARW", ".CR2", ".NEF", ".RAF", ".DNG", ".JPG", ".JPEG", ".TIFF"}:
                date_taken = self.extract_date_taken(file)
                if date_taken:
                    if earliest_date is None or date_taken < earliest_date:
                        earliest_date = date_taken
                        self.console.print(f"[bold green]✅ Date trouvée pour {source_path.name} : {date_taken.strftime('%d-%m-%Y')} (dans {file.name})[/bold green]")
        return earliest_date

    def ask_manual_date(self, source_name: str) -> str:
        """Ask the user to manually input a date for a specific source."""
        while True:
            date_str = Prompt.ask(
                f"[yellow]Aucune date trouvée pour {source_name}. Veuillez entrer la date manuellement (format : JJ-MM-AAAA)[/yellow]"
            )
            try:
                date_obj = datetime.strptime(date_str, "%d-%m-%Y")
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                self.console.print("[bold red]❌ Format invalide. Veuillez réessayer.[/bold red]")

    def list_disks(self):
        """List all available drives on the system."""
        partitions = psutil.disk_partitions()
        drives = [Path(part.mountpoint) for part in partitions if Path(part.mountpoint).exists()]
        return drives

    def select_drive(self):
        """Ask the user to select a drive."""
        drives = self.list_disks()
        self.console.print("\n[yellow]📁 Disques disponibles :[/yellow]")
        for idx, drive in enumerate(drives, start=1):
            self.console.print(f"[cyan]{idx}.[/cyan] {drive}")

        choice = IntPrompt.ask(
            "\n💾 Choisissez le disque où exporter le projet",
            choices=[str(i) for i in range(1, len(drives) + 1)],
        )
        return drives[choice - 1]

    def get_source_paths_and_names(self) -> dict:
        """Get multiple source folder paths and their corresponding project names from the user."""
        source_info = {}
        self.console.print("[yellow]Vous pouvez entrer jusqu'à 10 sources.[/yellow]")
        self.console.print("[cyan]Appuyez sur Entrée sans rien écrire pour terminer.[/cyan]")

        i = 0
        while i < 10:
            source_path_str = Prompt.ask(f"\n📂 Chemin du dossier source #{i+1}")
            if not source_path_str.strip():
                break

            source_path = Path(source_path_str)
            if not source_path.exists() or not source_path.is_dir():
                self.console.print("[bold red]❌ Chemin invalide ou introuvable. Veuillez réessayer.[/bold red]")
                continue  # Ne pas incrémenter i, permettre une nouvelle tentative

            project_name = Prompt.ask(f"📝 Nom du projet pour la source {source_path}")
            source_info[source_path] = {
                'name': self.sanitize_filename(project_name),
                'date': None  # La date sera définie plus tard
            }
            i += 1  # Incrémenter seulement si la source est valide

        if not source_info:
            self.console.print("[bold red]❌ Aucune source valide fournie. Annulation.[/bold red]")
            exit()

        return source_info

    def create_project_structure(self, base_path: Path, project_name: str):
        """Create the directory structure for the project."""
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

        self.console.print(f"[bold green]✅ Structure créée : {project_path}[/bold green]")
        return project_path

    def organize_files(self, source_path: Path, project_path: Path):
        """Organize files into the '02_RAW' folder for a specific source."""
        raw_folder = project_path / "02_RAW"
        raw_folder.mkdir(parents=True, exist_ok=True)

        for file in track(
            list(source_path.rglob("*")),
            description=f"Organisation des fichiers depuis {source_path}...",
        ):
            if file.is_file():
                destination = raw_folder / file.name

                # Gérer les collisions de noms de fichiers
                if destination.exists():
                    counter = 1
                    stem = file.stem
                    suffix = file.suffix
                    while destination.exists():
                        destination = raw_folder / f"{stem}_{counter}{suffix}"
                        counter += 1
                    self.console.print(f"[yellow]⚠️  Collision détectée : {file.name} renommé en {destination.name}[/yellow]")

                try:
                    shutil.copy2(file, destination)
                    self.logger.info(f"Fichier copié : {file} -> {destination}")
                except Exception as e:
                    self.logger.error(f"Erreur lors de la copie de {file}: {e}")
                    self.console.print(f"[bold red]❌ Erreur lors de la copie de {file.name}: {e}[/bold red]")

    def main(self):
        self.console.print(
            Panel(
                "[bold cyan]📸 Photo Pro Manager[/bold cyan]",
                subtitle="[italic]Simplifiez vos workflows photo[/italic]",
            )
        )

        # Obtenir les chemins source et noms de projets
        source_info = self.get_source_paths_and_names()

        # Trouver ou demander la date pour chaque source
        for source_path in source_info:
            date_obj = self.find_date_in_source(source_path)
            if date_obj:
                date_str = date_obj.strftime("%Y-%m-%d")
            else:
                date_str = self.ask_manual_date(source_path.name)
            source_info[source_path]['date'] = date_str

        # Sélectionner le disque d'exportation
        selected_drive = self.select_drive()

        # Créer la structure pour chaque source
        for source_path, info in source_info.items():
            base_path = selected_drive / "PROJETS_PHOTO" / info['date'].split("-")[0]
            base_path.mkdir(parents=True, exist_ok=True)
            
            project_folder_name = f"{info['date']}_{info['name']}"
            project_path = self.create_project_structure(base_path, project_folder_name)
            self.organize_files(source_path, project_path)

        self.console.print("[bold green]✨ Organisation terminée avec succès ![/bold green]")


if __name__ == "__main__":
    manager = PhotoProManager()
    manager.main()
