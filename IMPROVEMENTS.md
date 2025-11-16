# 🚀 PhotoFlow Master - Améliorations Possibles

Ce document détaille les améliorations qui peuvent être apportées au code actuel.

---

## 🔴 PRIORITÉ HAUTE (Impact majeur)

### 1. **Tests EXIF Réels avec Vraies Images**

**Problème:** Les tests actuels n'utilisent pas de vraies images avec métadonnées EXIF.

**Impact:** On ne teste pas vraiment l'extraction EXIF.

**Solution:**
```python
# tests/fixtures/create_test_images.py
from PIL import Image
from PIL.ExifTags import TAGS
import piexif
from datetime import datetime

def create_image_with_exif(path: Path, date: datetime) -> Path:
    """Créer une image avec vraies métadonnées EXIF."""
    img = Image.new('RGB', (100, 100), color='red')

    # Créer EXIF avec piexif
    exif_dict = {
        "0th": {},
        "Exif": {
            piexif.ExifIFD.DateTimeOriginal: date.strftime("%Y:%m:%d %H:%M:%S")
        }
    }

    exif_bytes = piexif.dump(exif_dict)
    img.save(path, exif=exif_bytes)
    return path

# Test
def test_exif_extraction_real_image(temp_dir):
    date = datetime(2023, 12, 31, 10, 30, 0)
    img_path = create_image_with_exif(temp_dir / "test.jpg", date)

    handler = EXIFHandler()
    extracted = handler.extract_date(img_path)

    assert extracted == date
```

**Effort:** 🔨 Moyen (2-3h)
**Bénéfice:** ⭐⭐⭐⭐⭐ Critique

---

### 2. **Configuration Externe (YAML/TOML)**

**Problème:** Toute la configuration est codée en dur dans `constants.py`.

**Impact:** Difficile de personnaliser sans modifier le code.

**Solution:**
```python
# config.toml
[photoflow]
max_sources = 10
max_workers = 4
exif_cache_size = 128

[project_structure]
raw_folder = "02_RAW"
selects_folder = "03_SELECTS"

[performance]
file_copy_buffer_size = 1048576
enable_concurrent_copy = true

# photoflow/config.py
import tomllib
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Config:
    max_sources: int = 10
    max_workers: int = 4
    exif_cache_size: int = 128

    @classmethod
    def load(cls, config_file: Path) -> 'Config':
        """Charger depuis fichier TOML."""
        with open(config_file, 'rb') as f:
            data = tomllib.load(f)
        return cls(**data['photoflow'])

    @classmethod
    def from_default(cls) -> 'Config':
        """Config par défaut."""
        return cls()

# Utilisation
config = Config.load(Path("config.toml"))
manager = PhotoFlowManager(max_workers=config.max_workers)
```

**Effort:** 🔨 Moyen (3-4h)
**Bénéfice:** ⭐⭐⭐⭐⭐ Très utile

---

### 3. **Retry Logic pour Opérations I/O**

**Problème:** Une erreur réseau temporaire fait échouer toute l'opération.

**Impact:** Manque de robustesse sur disques réseau/USB.

**Solution:**
```python
# photoflow/retry.py
import time
from functools import wraps
from typing import TypeVar, Callable

T = TypeVar('T')

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (IOError, OSError)
):
    """Décorateur de retry avec backoff exponentiel."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            attempt = 0
            current_delay = delay

            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise

                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff

            raise RuntimeError("Max retries exceeded")

        return wrapper
    return decorator

# Utilisation dans FileManager
@retry(max_attempts=3, delay=1.0)
def copy_file(self, source: Path, destination: Path) -> None:
    """Copie avec retry automatique."""
    shutil.copy2(source, destination)
```

**Effort:** 🔨 Facile (1-2h)
**Bénéfice:** ⭐⭐⭐⭐ Important

---

### 4. **Annulation d'Opérations en Cours**

**Problème:** Impossible d'annuler une opération longue dans la GUI.

**Impact:** Expérience utilisateur frustrante.

**Solution:**
```python
# photoflow/core.py
import threading

class CancellationToken:
    """Token pour annuler des opérations."""

    def __init__(self):
        self._cancelled = threading.Event()

    def cancel(self):
        """Marquer comme annulé."""
        self._cancelled.set()

    def is_cancelled(self) -> bool:
        """Vérifier si annulé."""
        return self._cancelled.is_set()

    def check_cancelled(self):
        """Lever exception si annulé."""
        if self.is_cancelled():
            raise CancellationError("Operation cancelled by user")

class PhotoFlowManager:
    def create_project(
        self,
        source: SourceInfo,
        base_drive: Path,
        cancellation_token: Optional[CancellationToken] = None,
        progress_callback: Optional[callable] = None,
    ) -> ProjectResult:
        """Créer projet avec support d'annulation."""
        token = cancellation_token or CancellationToken()

        # Vérifier à chaque étape
        token.check_cancelled()
        project_path = self.file_manager.create_project_structure(...)

        token.check_cancelled()
        results = self.file_manager.organize_files(
            ...,
            cancellation_token=token  # Propager aux sous-opérations
        )

        return result

# Dans GUI
class PhotoFlowGUI:
    def __init__(self):
        self._cancellation_token = CancellationToken()

    def cancel_processing(self):
        """Bouton annuler."""
        self._cancellation_token.cancel()
        self.log("⚠️ Annulation en cours...")

    def start_processing(self):
        self._cancellation_token = CancellationToken()
        # Passer le token au worker thread
        self._processing_thread = threading.Thread(
            target=self._process_worker,
            args=(self._cancellation_token,),
            daemon=True
        )
```

**Effort:** 🔨 Moyen (3-4h)
**Bénéfice:** ⭐⭐⭐⭐⭐ Essentiel pour UX

---

### 5. **Preview Avant Traitement**

**Problème:** L'utilisateur ne voit pas ce qui va être fait avant de lancer.

**Impact:** Risque d'erreurs, pas de contrôle.

**Solution:**
```python
# photoflow/preview.py
from dataclasses import dataclass
from typing import List

@dataclass
class ProjectPreview:
    """Aperçu d'un projet avant création."""
    source_path: Path
    project_name: str
    project_path: Path
    file_count: int
    total_size_gb: float
    estimated_time_seconds: float
    files_by_type: dict[str, int]  # {'.jpg': 50, '.raw': 20}
    warnings: List[str]

class PhotoFlowManager:
    def preview_project(self, source: SourceInfo, base_drive: Path) -> ProjectPreview:
        """Générer aperçu sans créer."""
        # Compter les fichiers
        files = list(self._iter_all_files(source.path))

        # Analyser types
        files_by_type = {}
        for f in files:
            ext = f.suffix.upper()
            files_by_type[ext] = files_by_type.get(ext, 0) + 1

        # Estimer taille
        total_size = sum(f.stat().st_size for f in files)

        # Estimer temps (basé sur benchmarks)
        estimated_time = len(files) * 0.1  # 100ms par fichier

        # Warnings
        warnings = []
        if total_size > 100 * 1024**3:  # > 100GB
            warnings.append("⚠️ Large project (>100GB)")

        year = source.date.split("-")[0]
        project_path = base_drive / "PROJETS_PHOTO" / year / f"{source.date}_{source.name}"

        return ProjectPreview(
            source_path=source.path,
            project_name=source.name,
            project_path=project_path,
            file_count=len(files),
            total_size_gb=total_size / (1024**3),
            estimated_time_seconds=estimated_time,
            files_by_type=files_by_type,
            warnings=warnings
        )

# Dans GUI - Dialog de confirmation
def show_preview_dialog(self, preview: ProjectPreview) -> bool:
    """Afficher dialog de preview."""
    dialog = tk.Toplevel(self.root)
    dialog.title("Preview - Confirmer l'opération")

    # Afficher les stats
    text = f"""
📊 Aperçu du Projet

Source: {preview.source_path}
Destination: {preview.project_path}

📁 Fichiers: {preview.file_count}
💾 Taille totale: {preview.total_size_gb:.2f} GB
⏱️  Temps estimé: {preview.estimated_time_seconds:.0f}s

Types de fichiers:
{chr(10).join(f'  • {ext}: {count}' for ext, count in preview.files_by_type.items())}

{chr(10).join(preview.warnings)}
"""

    ttk.Label(dialog, text=text, font=('Courier', 10)).pack(pady=10)

    # Boutons
    confirmed = [False]
    def on_confirm():
        confirmed[0] = True
        dialog.destroy()

    ttk.Button(dialog, text="✅ Confirmer", command=on_confirm).pack()
    ttk.Button(dialog, text="❌ Annuler", command=dialog.destroy).pack()

    dialog.wait_window()
    return confirmed[0]
```

**Effort:** 🔨 Moyen (4-5h)
**Bénéfice:** ⭐⭐⭐⭐⭐ Excellent pour UX

---

## 🟡 PRIORITÉ MOYENNE (Améliorations utiles)

### 6. **Rapport Détaillé Post-Traitement**

**Solution:**
```python
# photoflow/report.py
from datetime import datetime
import json

@dataclass
class ProcessingReport:
    """Rapport détaillé d'une opération."""
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    projects_created: int
    files_copied: int
    files_failed: int
    files_renamed: int
    total_size_gb: float
    errors: List[dict]

    def to_html(self) -> str:
        """Générer rapport HTML."""
        return f"""
<!DOCTYPE html>
<html>
<head><title>PhotoFlow Report</title></head>
<body>
    <h1>📊 Rapport PhotoFlow Master</h1>
    <p>Date: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>Durée: {self.duration_seconds:.1f}s</p>

    <h2>Résumé</h2>
    <ul>
        <li>Projets créés: {self.projects_created}</li>
        <li>Fichiers copiés: {self.files_copied}</li>
        <li>Fichiers échoués: {self.files_failed}</li>
        <li>Taille totale: {self.total_size_gb:.2f} GB</li>
    </ul>

    <h2>Erreurs</h2>
    <ul>
        {"".join(f"<li>{e['file']}: {e['error']}</li>" for e in self.errors)}
    </ul>
</body>
</html>
"""

    def save(self, path: Path):
        """Sauvegarder rapport."""
        path.write_text(self.to_html())
```

**Effort:** 🔨 Facile (2h)
**Bénéfice:** ⭐⭐⭐ Utile

---

### 7. **Détection de Doublons**

**Problème:** Peut copier le même fichier plusieurs fois.

**Solution:**
```python
# photoflow/deduplication.py
import hashlib

class FileDeduplicator:
    """Détecteur de doublons par hash."""

    def __init__(self):
        self._hashes: dict[str, Path] = {}

    def compute_hash(self, file_path: Path) -> str:
        """Calculer SHA256 d'un fichier."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def is_duplicate(self, file_path: Path) -> Optional[Path]:
        """Vérifier si fichier est un doublon."""
        file_hash = self.compute_hash(file_path)

        if file_hash in self._hashes:
            return self._hashes[file_hash]  # Chemin du doublon

        self._hashes[file_hash] = file_path
        return None

# Utilisation
dedup = FileDeduplicator()
for file in files:
    duplicate_of = dedup.is_duplicate(file)
    if duplicate_of:
        logger.warning(f"Duplicate: {file} = {duplicate_of}")
        # Option: skip ou créer lien symbolique
    else:
        copy_file(file)
```

**Effort:** 🔨 Moyen (3h)
**Bénéfice:** ⭐⭐⭐⭐ Important

---

### 8. **Historique des Opérations (SQLite)**

**Solution:**
```python
# photoflow/history.py
import sqlite3
from datetime import datetime

class OperationHistory:
    """Historique des opérations."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Créer schéma."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS operations (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                operation_type TEXT,
                source_path TEXT,
                dest_path TEXT,
                files_count INTEGER,
                success BOOLEAN,
                error_message TEXT
            )
        """)
        conn.commit()
        conn.close()

    def log_operation(self, op_type: str, source: Path, dest: Path,
                      files_count: int, success: bool, error: str = None):
        """Enregistrer opération."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """INSERT INTO operations VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(), op_type, str(source),
             str(dest), files_count, success, error)
        )
        conn.commit()
        conn.close()

    def get_history(self, limit: int = 100) -> List[dict]:
        """Récupérer historique."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT * FROM operations ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        results = cursor.fetchall()
        conn.close()
        return results
```

**Effort:** 🔨 Moyen (4h)
**Bénéfice:** ⭐⭐⭐ Utile pour audit

---

### 9. **Génération de Thumbnails**

**Solution:**
```python
# photoflow/thumbnails.py
from PIL import Image

class ThumbnailGenerator:
    """Générateur de vignettes."""

    def generate(self, image_path: Path, thumb_dir: Path,
                 size: tuple[int, int] = (200, 200)):
        """Générer thumbnail."""
        with Image.open(image_path) as img:
            img.thumbnail(size)
            thumb_path = thumb_dir / f"thumb_{image_path.name}"
            img.save(thumb_path, "JPEG", quality=85)
            return thumb_path

    def generate_for_project(self, project_path: Path):
        """Générer thumbnails pour tout un projet."""
        raw_folder = project_path / "02_RAW"
        thumb_folder = project_path / "thumbnails"
        thumb_folder.mkdir(exist_ok=True)

        for img in raw_folder.glob("*.jpg"):
            try:
                self.generate(img, thumb_folder)
            except Exception as e:
                logger.warning(f"Failed to generate thumb for {img}: {e}")
```

**Effort:** 🔨 Facile (2h)
**Bénéfice:** ⭐⭐⭐ Utile

---

## 🟢 PRIORITÉ BASSE (Nice to have)

### 10. **Support Async/Await**

**Pour I/O vraiment asynchrone:**
```python
import asyncio
import aiofiles

async def copy_file_async(source: Path, dest: Path):
    """Copie asynchrone."""
    async with aiofiles.open(source, 'rb') as src:
        async with aiofiles.open(dest, 'wb') as dst:
            await dst.write(await src.read())
```

**Effort:** 🔨🔨 Difficile (10h+)
**Bénéfice:** ⭐⭐ Overkill pour la plupart des cas

---

### 11. **Interface Web (FastAPI)**

**Pour accès distant:**
```python
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()

@app.post("/api/projects/create")
async def create_project(source: SourceInfo, background_tasks: BackgroundTasks):
    """API pour créer projet."""
    background_tasks.add_task(manager.create_project, source)
    return {"status": "processing"}
```

**Effort:** 🔨🔨🔨 Très difficile (20h+)
**Bénéfice:** ⭐⭐ Niche

---

### 12. **Plugin System**

**Pour extensibilité:**
```python
# photoflow/plugins.py
class PluginBase:
    """Base pour plugins."""

    def on_before_copy(self, file: Path) -> bool:
        """Hook avant copie. Return False to skip."""
        return True

    def on_after_copy(self, source: Path, dest: Path):
        """Hook après copie."""
        pass

class WatermarkPlugin(PluginBase):
    """Plugin pour ajouter watermark."""

    def on_after_copy(self, source: Path, dest: Path):
        """Ajouter watermark."""
        if dest.suffix.lower() in {'.jpg', '.png'}:
            add_watermark(dest)
```

**Effort:** 🔨🔨 Difficile (8h)
**Bénéfice:** ⭐⭐⭐ Pour utilisateurs avancés

---

## 📊 Tableau Récapitulatif

| # | Amélioration | Priorité | Effort | Bénéfice | Impact |
|---|--------------|----------|--------|----------|--------|
| 1 | Tests EXIF réels | 🔴 HAUTE | 🔨 Moyen | ⭐⭐⭐⭐⭐ | Qualité |
| 2 | Config externe | 🔴 HAUTE | 🔨 Moyen | ⭐⭐⭐⭐⭐ | Flexibilité |
| 3 | Retry logic | 🔴 HAUTE | 🔨 Facile | ⭐⭐⭐⭐ | Robustesse |
| 4 | Annulation | 🔴 HAUTE | 🔨 Moyen | ⭐⭐⭐⭐⭐ | UX |
| 5 | Preview | 🔴 HAUTE | 🔨 Moyen | ⭐⭐⭐⭐⭐ | UX |
| 6 | Rapports | 🟡 MOYENNE | 🔨 Facile | ⭐⭐⭐ | Traçabilité |
| 7 | Déduplication | 🟡 MOYENNE | 🔨 Moyen | ⭐⭐⭐⭐ | Efficacité |
| 8 | Historique DB | 🟡 MOYENNE | 🔨 Moyen | ⭐⭐⭐ | Audit |
| 9 | Thumbnails | 🟡 MOYENNE | 🔨 Facile | ⭐⭐⭐ | UX |
| 10 | Async/await | 🟢 BASSE | 🔨🔨 Difficile | ⭐⭐ | Performance |
| 11 | Web API | 🟢 BASSE | 🔨🔨🔨 Très diff. | ⭐⭐ | Niche |
| 12 | Plugins | 🟢 BASSE | 🔨🔨 Difficile | ⭐⭐⭐ | Extensibilité |

---

## 🎯 Recommandation : Plan d'Action

### Sprint 1 (1 semaine)
1. ✅ Tests EXIF réels avec piexif
2. ✅ Configuration externe (TOML)
3. ✅ Retry logic

### Sprint 2 (1 semaine)
4. ✅ Support annulation
5. ✅ Preview avant traitement

### Sprint 3 (1 semaine)
6. ✅ Détection doublons
7. ✅ Rapports HTML
8. ✅ Thumbnails

---

**Questions à vous poser:**
- Utilisez-vous souvent des disques réseau ? → Priorité Retry
- Avez-vous beaucoup de doublons ? → Priorité Déduplication
- Voulez-vous partager avec une équipe ? → Considérer Web API
- Besoin de personnalisation ? → Config externe + Plugins

**Voulez-vous que j'implémente certaines de ces améliorations ?** 🚀
