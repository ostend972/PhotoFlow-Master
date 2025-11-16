#!/usr/bin/env python3
"""
PhotoFlow Master - GUI Interface (Improved)
Modern graphical interface with safe threading and better error handling.
"""

import queue
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

import psutil

from photoflow import (
    PhotoFlowManager,
    SourceInfo,
    ProjectResult,
    setup_logging,
    get_logger,
    validate_date_format,
    PhotoFlowError,
)
from photoflow.constants import (
    GUI_WINDOW_SIZE,
    GUI_TITLE,
    GUI_LOG_HEIGHT,
    GUI_TREE_HEIGHT,
    MAX_SOURCES,
    USER_DATE_FORMAT,
    ISO_DATE_FORMAT,
)


logger = get_logger(__name__)


class PhotoFlowGUI:
    """Graphical user interface for PhotoFlow Master."""

    def __init__(self, root: tk.Tk):
        """
        Initialize GUI.

        Args:
            root: Root Tkinter window
        """
        self.root = root
        self.root.title(GUI_TITLE)
        self.root.geometry(f"{GUI_WINDOW_SIZE[0]}x{GUI_WINDOW_SIZE[1]}")
        self.root.resizable(True, True)

        # Manager
        self.manager = PhotoFlowManager()

        # Data
        self.sources: list[SourceInfo] = []

        # Threading
        self._processing_thread: Optional[threading.Thread] = None
        self._stop_processing = threading.Event()
        self._message_queue: queue.Queue = queue.Queue()

        # Setup
        self.setup_style()
        self.create_widgets()
        self.refresh_drives()

        # Start message queue processor
        self.process_message_queue()

    def setup_style(self) -> None:
        """Configure UI style."""
        style = ttk.Style()
        style.theme_use('clam')

        # Custom styles
        style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'), foreground='#2c3e50')
        style.configure('Subtitle.TLabel', font=('Helvetica', 10, 'italic'), foreground='#7f8c8d')
        style.configure('Header.TLabel', font=('Helvetica', 12, 'bold'), foreground='#34495e')
        style.configure('Action.TButton', font=('Helvetica', 10), padding=10)

    def create_widgets(self) -> None:
        """Create all UI widgets."""
        # Header
        header_frame = ttk.Frame(self.root, padding="20")
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), columnspan=2)

        ttk.Label(
            header_frame,
            text="📸 PhotoFlow Master v2.0",
            style='Title.TLabel'
        ).grid(row=0, column=0, sticky=tk.W)

        ttk.Label(
            header_frame,
            text="Professional Photo Project Manager - Refactored Edition",
            style='Subtitle.TLabel'
        ).grid(row=1, column=0, sticky=tk.W)

        # Separator
        ttk.Separator(self.root, orient='horizontal').grid(
            row=1, column=0, sticky=(tk.W, tk.E), columnspan=2, pady=10
        )

        # Left panel - Sources
        left_frame = ttk.LabelFrame(self.root, text="Sources & Projects", padding="10")
        left_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)

        # Sources tree
        self.sources_tree = ttk.Treeview(
            left_frame,
            columns=('Name', 'Date', 'Path'),
            show='headings',
            height=GUI_TREE_HEIGHT
        )
        self.sources_tree.heading('Name', text='Project Name')
        self.sources_tree.heading('Date', text='Date')
        self.sources_tree.heading('Path', text='Source Path')
        self.sources_tree.column('Name', width=150)
        self.sources_tree.column('Date', width=100)
        self.sources_tree.column('Path', width=200)
        self.sources_tree.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.sources_tree.yview)
        scrollbar.grid(row=0, column=2, sticky=(tk.N, tk.S))
        self.sources_tree.configure(yscrollcommand=scrollbar.set)

        # Buttons
        ttk.Button(
            left_frame,
            text="➕ Add Source",
            command=self.add_source
        ).grid(row=1, column=0, sticky=(tk.W, tk.E), padx=2, pady=5)

        ttk.Button(
            left_frame,
            text="➖ Remove",
            command=self.remove_source
        ).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=2, pady=5)

        # Right panel - Configuration
        right_frame = ttk.LabelFrame(self.root, text="Configuration", padding="10")
        right_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)

        # Drive selection
        ttk.Label(
            right_frame,
            text="Destination Drive:",
            font=('Helvetica', 10, 'bold')
        ).grid(row=0, column=0, sticky=tk.W, pady=5)

        self.drive_var = tk.StringVar()
        self.drive_combo = ttk.Combobox(
            right_frame,
            textvariable=self.drive_var,
            state='readonly',
            width=30
        )
        self.drive_combo.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)

        ttk.Button(
            right_frame,
            text="🔄 Refresh",
            command=self.refresh_drives
        ).grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)

        # Info frame
        info_frame = ttk.LabelFrame(right_frame, text="Project Structure", padding="10")
        info_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        structure_text = """📁 DRIVE/PROJETS_PHOTO/YEAR/DATE_NAME/
├── 01_PRE-PRODUCTION
│   ├── Moodboard
│   ├── References
│   └── Brief
├── 02_RAW (source files)
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

        ttk.Label(
            info_frame,
            text=structure_text,
            font=('Courier', 8),
            justify=tk.LEFT
        ).grid(row=0, column=0, sticky=tk.W)

        # Log frame
        log_frame = ttk.LabelFrame(self.root, text="Activity Log", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=GUI_LOG_HEIGHT,
            width=80,
            state='disabled',
            bg='#ecf0f1',
            font=('Courier', 9)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Progress bar
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=5)

        # Action button
        self.btn_process = ttk.Button(
            self.root,
            text="🚀 START ORGANIZATION",
            command=self.start_processing,
            style='Action.TButton'
        )
        self.btn_process.grid(row=5, column=0, columnspan=2, pady=20)

        # Configure grid weights
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

    def log(self, message: str, level: str = 'info') -> None:
        """
        Add message to activity log (thread-safe).

        Args:
            message: Message to log
            level: Log level (info, warning, error)
        """
        self._message_queue.put(('log', message, level))

    def _log_internal(self, message: str, level: str) -> None:
        """Internal log method (runs on main thread)."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}\n"

        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, formatted)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

        # Also log to file
        if level == 'info':
            logger.info(message)
        elif level == 'warning':
            logger.warning(message)
        elif level == 'error':
            logger.error(message)

    def refresh_drives(self) -> None:
        """Refresh list of available drives."""
        partitions = psutil.disk_partitions()
        drives = [
            Path(part.mountpoint)
            for part in partitions
            if Path(part.mountpoint).exists()
        ]

        drive_strings = []
        for drive in drives:
            try:
                usage = psutil.disk_usage(str(drive))
                free_gb = usage.free / (1024 ** 3)
                drive_strings.append(f"{drive} ({free_gb:.1f} GB free)")
            except Exception:
                drive_strings.append(str(drive))

        self.drive_combo['values'] = drive_strings
        if drives:
            self.drive_combo.current(0)

        self.log(f"🔄 {len(drives)} drive(s) detected")

    def add_source(self) -> None:
        """Add a new source via dialog."""
        if len(self.sources) >= MAX_SOURCES:
            messagebox.showwarning(
                "Limit Reached",
                f"Maximum {MAX_SOURCES} sources allowed."
            )
            return

        # Select directory
        source_path = filedialog.askdirectory(title="Select Source Directory")
        if not source_path:
            return

        source_path = Path(source_path)

        # Dialog for project details
        dialog = tk.Toplevel(self.root)
        dialog.title("New Project")
        dialog.geometry("500x250")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(
            dialog,
            text=f"Source: {source_path.name}",
            font=('Helvetica', 10, 'bold')
        ).pack(pady=10)

        # Project name
        ttk.Label(dialog, text="Project Name:").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.pack(pady=5)
        name_entry.insert(0, source_path.name)
        name_entry.focus()

        # Date
        ttk.Label(
            dialog,
            text=f"Date ({USER_DATE_FORMAT}) - leave empty for auto-detection:"
        ).pack(pady=5)
        date_entry = ttk.Entry(dialog, width=40)
        date_entry.pack(pady=5)

        def on_ok():
            project_name = name_entry.get().strip()
            date_str = date_entry.get().strip()

            if not project_name:
                messagebox.showerror("Error", "Project name cannot be empty.")
                return

            # Validate date if provided
            date_iso: Optional[str] = None
            if date_str:
                if not validate_date_format(date_str, USER_DATE_FORMAT):
                    messagebox.showerror(
                        "Error",
                        f"Invalid date format. Use {USER_DATE_FORMAT}"
                    )
                    return
                date_obj = datetime.strptime(date_str, USER_DATE_FORMAT)
                date_iso = date_obj.strftime(ISO_DATE_FORMAT)

            # Create SourceInfo
            try:
                source_info = SourceInfo(
                    path=source_path,
                    name=project_name,
                    date=date_iso
                )
                self.sources.append(source_info)

                # Add to tree
                display_date = date_iso or "AUTO"
                self.sources_tree.insert(
                    '',
                    tk.END,
                    values=(project_name, display_date, str(source_path))
                )
                self.log(f"➕ Source added: {project_name}")
                dialog.destroy()

            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(dialog, text="✅ Add", command=on_ok).pack(pady=10)
        dialog.bind('<Return>', lambda e: on_ok())

    def remove_source(self) -> None:
        """Remove selected source."""
        selection = self.sources_tree.selection()
        if not selection:
            messagebox.showwarning(
                "No Selection",
                "Please select a source to remove."
            )
            return

        item = selection[0]
        index = self.sources_tree.index(item)

        self.sources_tree.delete(item)
        removed = self.sources.pop(index)
        self.log(f"➖ Source removed: {removed.name}")

    def start_processing(self) -> None:
        """Start processing in a background thread."""
        # Validate
        if not self.sources:
            messagebox.showerror("Error", "No sources added.")
            return

        if not self.drive_var.get():
            messagebox.showerror("Error", "No destination drive selected.")
            return

        # Disable UI
        self.btn_process.config(state='disabled')
        self.progress.start()

        # Reset stop event
        self._stop_processing.clear()

        # Start thread
        self._processing_thread = threading.Thread(
            target=self._process_worker,
            daemon=True
        )
        self._processing_thread.start()

    def _process_worker(self) -> None:
        """Worker thread for processing (runs in background)."""
        try:
            # Extract drive path from combo text
            drive_text = self.drive_var.get()
            drive_path = Path(drive_text.split(' ')[0])

            self.log("🚀 Processing started...")

            # Auto-detect dates
            for source in self.sources:
                if self._stop_processing.is_set():
                    self.log("⚠️ Processing cancelled")
                    return

                if not source.date:
                    self.log(f"🔍 Detecting date for {source.name}...")

                    def date_callback(file_path, date):
                        self.log(
                            f"  ✅ Found: {date.strftime(USER_DATE_FORMAT)} "
                            f"in {file_path.name}"
                        )

                    source.date = self.manager.detect_date(source, callback=date_callback)

                    if not source.date:
                        # Need manual input
                        self._message_queue.put(('ask_date', source))
                        return  # Wait for manual input

            # Create projects
            for idx, source in enumerate(self.sources, 1):
                if self._stop_processing.is_set():
                    self.log("⚠️ Processing cancelled")
                    return

                self.log(f"📂 Processing {source.name} ({idx}/{len(self.sources)})...")

                def copy_callback(completed, total, current_file):
                    if completed % 10 == 0:
                        self.log(f"  Copying: {current_file.name} ({completed}/{total})")

                result: ProjectResult = self.manager.create_project(
                    source,
                    drive_path,
                    progress_callback=copy_callback
                )

                if result.success:
                    self.log(
                        f"✅ {source.name}: {result.files_copied} files copied "
                        f"({result.files_renamed} renamed)",
                        'info'
                    )
                else:
                    self.log(f"❌ {source.name}: {result.error}", 'error')

            # Success
            self.log("✨ Organization completed successfully!")
            self._message_queue.put(('complete', None))

        except PhotoFlowError as e:
            self.log(f"❌ Error: {e}", 'error')
            self._message_queue.put(('error', str(e)))

        except Exception as e:
            self.log(f"❌ Unexpected error: {e}", 'error')
            logger.exception("Unexpected error in worker thread")
            self._message_queue.put(('error', str(e)))

        finally:
            self._message_queue.put(('done', None))

    def process_message_queue(self) -> None:
        """Process messages from worker thread (runs on main thread)."""
        try:
            while True:
                msg_type, *args = self._message_queue.get_nowait()

                if msg_type == 'log':
                    message, level = args
                    self._log_internal(message, level)

                elif msg_type == 'ask_date':
                    source = args[0]
                    self._ask_manual_date(source)

                elif msg_type == 'complete':
                    messagebox.showinfo(
                        "Success",
                        "All projects organized successfully!"
                    )

                elif msg_type == 'error':
                    error = args[0]
                    messagebox.showerror("Error", error)

                elif msg_type == 'done':
                    self.progress.stop()
                    self.btn_process.config(state='normal')

        except queue.Empty:
            pass

        # Schedule next check
        self.root.after(100, self.process_message_queue)

    def _ask_manual_date(self, source: SourceInfo) -> None:
        """Ask for manual date input (runs on main thread)."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Manual Date Required")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(
            dialog,
            text=f"No date found for: {source.name}",
            font=('Helvetica', 10, 'bold')
        ).pack(pady=10)

        ttk.Label(
            dialog,
            text=f"Enter date ({USER_DATE_FORMAT}):"
        ).pack(pady=5)

        date_entry = ttk.Entry(dialog, width=30)
        date_entry.pack(pady=5)
        date_entry.focus()

        def on_ok():
            date_str = date_entry.get().strip()

            if not validate_date_format(date_str, USER_DATE_FORMAT):
                messagebox.showerror(
                    "Error",
                    f"Invalid date format. Use {USER_DATE_FORMAT}"
                )
                return

            date_obj = datetime.strptime(date_str, USER_DATE_FORMAT)
            source.date = date_obj.strftime(ISO_DATE_FORMAT)
            self.log(f"✅ Manual date set: {date_str} for {source.name}")
            dialog.destroy()

            # Restart processing
            self._processing_thread = threading.Thread(
                target=self._process_worker,
                daemon=True
            )
            self._processing_thread.start()

        ttk.Button(dialog, text="✅ Confirm", command=on_ok).pack(pady=10)
        dialog.bind('<Return>', lambda e: on_ok())

    def on_closing(self) -> None:
        """Handle window closing."""
        if self._processing_thread and self._processing_thread.is_alive():
            if messagebox.askokcancel(
                "Quit",
                "Processing in progress. Are you sure you want to quit?"
            ):
                self._stop_processing.set()
                self.root.destroy()
        else:
            self.root.destroy()


def main() -> None:
    """Main entry point."""
    # Setup logging
    setup_logging(log_to_console=False)

    # Create and run GUI
    root = tk.Tk()
    app = PhotoFlowGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
