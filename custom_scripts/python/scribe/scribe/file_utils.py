import os
import re
import datetime
from pathlib import Path
from typing import Optional
from InquirerPy import inquirer
from rich import print as rprint

def get_daily_log_path(kb_base_dir: Path) -> Path:
    """Gets the expected path for today's daily log."""
    today = datetime.date.today()
    date_str = today.strftime("%Y-%m-%d")
    return kb_base_dir / "daily" / f"{date_str}.md"

def sanitize_filename(title: str) -> str:
    """Sanitizes a title into a safe filename."""
    # Convert to lowercase
    sanitized = title.lower()
    # Replace spaces and consecutive hyphens/underscores with a single underscore
    sanitized = re.sub(r'[\s_-]+', '_', sanitized)
    # Remove invalid filename characters
    sanitized = re.sub(r'[^\w\-.]', '', sanitized)
    # Remove leading/trailing underscores/hyphens
    sanitized = sanitized.strip('_')
    return sanitized + ".md"

def prompt_for_title() -> Optional[str]:
    """Prompts user for title and confirms."""
    while True:
        try:
            title = inquirer.text(
                message="Enter a title for the new note:",
                validate=lambda result: len(result) > 0,
                invalid_message="Title cannot be empty.",
            ).execute()

            if not title: # Should not happen with validation, but safety first
                return None

            confirm = inquirer.confirm(
                message=f"Use title: '{title}'?",
                default=True,
            ).execute()

            if confirm:
                return title
            # If not confirmed, the loop continues

        except KeyboardInterrupt:
            return None # User cancelled

def create_note_from_template(template_path: Path, target_path: Path, title: Optional[str] = None) -> bool:
    """Creates a new note file by populating a template."""
    try:
        # Read template content
        template_content = template_path.read_text()

        # Populate placeholders
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        final_title = title if title else today_str # Use date for daily title placeholder

        populated_content = template_content.replace("{{DATE}}", today_str)
        populated_content = populated_content.replace("{{DATETIME}}", now_str)
        populated_content = populated_content.replace("{{title}}", final_title)

        # Ensure target directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the new file
        target_path.write_text(populated_content)
        return True

    except FileNotFoundError:
        rprint(f"[bold red]Error:[/bold red] Template file not found: {template_path}")
        return False
    except IOError as e:
        rprint(f"[bold red]Error:[/bold red] Could not write file {target_path}: {e}")
        return False
    except Exception as e:
        rprint(f"[bold red]Error:[/bold red] An unexpected error occurred during file creation: {e}")
        return False

def open_in_editor(filepath: Path):
    """Opens the specified file in the default editor."""
    editor = os.environ.get('EDITOR')
    if not editor:
        # Fallback logic if EDITOR is not set (try common ones)
        for potential_editor in ['vim', 'nvim', 'nano', 'code', 'emacs']:
             if os.system(f'command -v {potential_editor} > /dev/null 2>&1') == 0:
                  editor = potential_editor
                  break

    if editor:
        try:
            import subprocess
            subprocess.run([editor, str(filepath)])
        except Exception as e:
            rprint(f"[bold yellow]Warning:[/bold yellow] Failed to open file in editor '{editor}': {e}")
            rprint(f"File path: {filepath}")
    else:
        rprint("[bold yellow]Warning:[/bold yellow] $EDITOR environment variable not set. Cannot open file.")
        rprint(f"File path: {filepath}")
