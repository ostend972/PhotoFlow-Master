#!/usr/bin/env python3
"""
PhotoFlow Master - CLI Interface
Command-line interface for professional photo project management.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import psutil
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

from photoflow import (
    PhotoFlowManager,
    SourceInfo,
    setup_logging,
    get_logger,
    validate_date_format,
    PhotoFlowError,
    NoSourcesError,
)
from photoflow.constants import MAX_SOURCES, USER_DATE_FORMAT, ISO_DATE_FORMAT


logger = get_logger(__name__)


class PhotoFlowCLI:
    """Command-line interface for PhotoFlow Master."""

    def __init__(self):
        """Initialize CLI interface."""
        self.console = Console()
        self.manager = PhotoFlowManager()
        self.sources: list[SourceInfo] = []

    def display_header(self) -> None:
        """Display application header."""
        self.console.print(
            Panel(
                "[bold cyan]📸 PhotoFlow Master v2.0[/bold cyan]\n"
                "[italic]Professional Photo Project Manager[/italic]",
                subtitle="[dim]Powered by Python & Rich[/dim]",
            )
        )

    def get_source_paths_and_names(self) -> list[SourceInfo]:
        """
        Prompt user for source directories and project names.

        Returns:
            List of SourceInfo objects
        """
        sources: list[SourceInfo] = []

        self.console.print(f"\n[yellow]📂 You can add up to {MAX_SOURCES} sources.[/yellow]")
        self.console.print("[cyan]Press Enter without input to finish.[/cyan]\n")

        i = 0
        while i < MAX_SOURCES:
            source_path_str = Prompt.ask(
                f"[bold]Source folder #{i + 1}[/bold]",
                default=""
            )

            # Empty input = done
            if not source_path_str.strip():
                break

            # Validate path
            source_path = Path(source_path_str).expanduser()

            if not source_path.exists() or not source_path.is_dir():
                self.console.print(
                    "[bold red]❌ Invalid path or directory not found. Please try again.[/bold red]"
                )
                continue  # Don't increment i, allow retry

            # Get project name
            default_name = source_path.name
            project_name = Prompt.ask(
                f"[bold]Project name for '{source_path.name}'[/bold]",
                default=default_name
            )

            # Get optional date
            date_str = Prompt.ask(
                f"[bold]Date ({USER_DATE_FORMAT}) - leave empty for auto-detection[/bold]",
                default=""
            )

            date_iso: Optional[str] = None
            if date_str.strip():
                if validate_date_format(date_str, USER_DATE_FORMAT):
                    date_obj = datetime.strptime(date_str, USER_DATE_FORMAT)
                    date_iso = date_obj.strftime(ISO_DATE_FORMAT)
                else:
                    self.console.print(
                        f"[yellow]⚠️  Invalid date format. Auto-detection will be used.[/yellow]"
                    )

            # Create SourceInfo
            try:
                source_info = SourceInfo(
                    path=source_path,
                    name=project_name,
                    date=date_iso
                )
                sources.append(source_info)
                self.console.print(
                    f"[bold green]✅ Source added: {project_name}[/bold green]\n"
                )
                i += 1  # Only increment on success

            except Exception as e:
                self.console.print(
                    f"[bold red]❌ Error: {e}[/bold red]"
                )
                continue

        return sources

    def list_drives(self) -> list[Path]:
        """
        List available disk drives.

        Returns:
            List of drive paths
        """
        partitions = psutil.disk_partitions()
        drives = [
            Path(part.mountpoint)
            for part in partitions
            if Path(part.mountpoint).exists()
        ]
        return drives

    def select_drive(self) -> Path:
        """
        Prompt user to select a destination drive.

        Returns:
            Selected drive path
        """
        drives = self.list_drives()

        if not drives:
            self.console.print("[bold red]❌ No drives found![/bold red]")
            sys.exit(1)

        self.console.print("\n[yellow]📁 Available drives:[/yellow]")
        for idx, drive in enumerate(drives, start=1):
            try:
                usage = psutil.disk_usage(str(drive))
                free_gb = usage.free / (1024 ** 3)
                total_gb = usage.total / (1024 ** 3)
                self.console.print(
                    f"[cyan]{idx}.[/cyan] {drive} "
                    f"[dim]({free_gb:.1f} GB free / {total_gb:.1f} GB total)[/dim]"
                )
            except Exception:
                self.console.print(f"[cyan]{idx}.[/cyan] {drive}")

        choice = IntPrompt.ask(
            "\n💾 Select destination drive",
            choices=[str(i) for i in range(1, len(drives) + 1)],
        )

        return drives[choice - 1]

    def ask_manual_date(self, source_name: str) -> str:
        """
        Ask user for manual date input.

        Args:
            source_name: Name of the source

        Returns:
            Date in ISO format
        """
        while True:
            date_str = Prompt.ask(
                f"[yellow]No date found for '{source_name}'. "
                f"Please enter date ({USER_DATE_FORMAT})[/yellow]"
            )

            if validate_date_format(date_str, USER_DATE_FORMAT):
                date_obj = datetime.strptime(date_str, USER_DATE_FORMAT)
                return date_obj.strftime(ISO_DATE_FORMAT)

            self.console.print(
                f"[bold red]❌ Invalid format. Use {USER_DATE_FORMAT}[/bold red]"
            )

    def process_sources(self, sources: list[SourceInfo], destination: Path) -> None:
        """
        Process all sources and create projects.

        Args:
            sources: List of source information
            destination: Destination drive
        """
        total_sources = len(sources)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        ) as progress:

            # Auto-detect dates
            detect_task = progress.add_task(
                "[cyan]Detecting dates...", total=total_sources
            )

            for source in sources:
                if not source.date:
                    progress.update(
                        detect_task,
                        description=f"[cyan]Detecting date for {source.name}..."
                    )

                    def date_callback(file_path, date):
                        self.console.print(
                            f"[green]  ✅ Found: {date.strftime(USER_DATE_FORMAT)} "
                            f"in {file_path.name}[/green]"
                        )

                    source.date = self.manager.detect_date(source, callback=date_callback)

                    if not source.date:
                        # Ask manually
                        progress.stop()
                        source.date = self.ask_manual_date(source.name)
                        progress.start()

                progress.advance(detect_task)

            progress.update(detect_task, description="[green]✅ Date detection complete")

            # Create projects
            project_task = progress.add_task(
                "[cyan]Creating projects...", total=total_sources
            )

            for idx, source in enumerate(sources, 1):
                progress.update(
                    project_task,
                    description=f"[cyan]Processing {source.name} ({idx}/{total_sources})..."
                )

                def copy_callback(completed, total, current_file):
                    if completed % 10 == 0:  # Update every 10 files
                        self.console.print(
                            f"  [dim]Copying: {current_file.name} ({completed}/{total})[/dim]"
                        )

                result = self.manager.create_project(
                    source,
                    destination,
                    progress_callback=copy_callback
                )

                if result.success:
                    self.console.print(
                        f"[bold green]✅ {source.name}: {result.files_copied} files copied "
                        f"({result.files_renamed} renamed)[/bold green]"
                    )
                else:
                    self.console.print(
                        f"[bold red]❌ {source.name}: Failed - {result.error}[/bold red]"
                    )

                progress.advance(project_task)

            progress.update(project_task, description="[green]✅ All projects complete!")

    def run(self) -> None:
        """Run the CLI application."""
        try:
            # Display header
            self.display_header()

            # Get sources
            self.console.print("\n[bold]Step 1: Add Source Directories[/bold]")
            sources = self.get_source_paths_and_names()

            if not sources:
                raise NoSourcesError()

            # Select destination
            self.console.print("\n[bold]Step 2: Select Destination Drive[/bold]")
            destination = self.select_drive()

            # Confirm
            self.console.print("\n[bold yellow]📋 Summary:[/bold yellow]")
            self.console.print(f"  • Sources: {len(sources)}")
            self.console.print(f"  • Destination: {destination}")

            confirm = Prompt.ask(
                "\n[bold]Proceed with organization?[/bold]",
                choices=["y", "n"],
                default="y"
            )

            if confirm.lower() != "y":
                self.console.print("[yellow]Operation cancelled.[/yellow]")
                return

            # Process
            self.console.print("\n[bold]Step 3: Processing...[/bold]")
            self.process_sources(sources, destination)

            # Success
            self.console.print(
                "\n[bold green]✨ Organization completed successfully![/bold green]"
            )

            # Cache stats
            stats = self.manager.get_cache_stats()
            self.console.print(
                f"\n[dim]EXIF Cache: {stats['hits']} hits, {stats['misses']} misses, "
                f"{stats['hit_rate']:.1%} hit rate[/dim]"
            )

        except NoSourcesError:
            self.console.print("[bold red]❌ No sources provided. Exiting.[/bold red]")
            sys.exit(1)

        except PhotoFlowError as e:
            self.console.print(f"[bold red]❌ Error: {e}[/bold red]")
            logger.exception("PhotoFlow error occurred")
            sys.exit(1)

        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠️  Operation interrupted by user.[/yellow]")
            sys.exit(130)

        except Exception as e:
            self.console.print(f"[bold red]❌ Unexpected error: {e}[/bold red]")
            logger.exception("Unexpected error occurred")
            sys.exit(1)


def main() -> None:
    """Main entry point."""
    # Setup logging
    setup_logging(log_to_console=False)

    # Run CLI
    cli = PhotoFlowCLI()
    cli.run()


if __name__ == "__main__":
    main()
