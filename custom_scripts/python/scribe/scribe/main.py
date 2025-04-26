import typer
from pathlib import Path
from typing_extensions import Annotated # Use typing.Annotated in Python 3.9+
from rich import print as rprint

from scribe import templates, file_utils # Use relative imports within the package

# --- Configuration ---
# Assume knowledge base is always here
KB_BASE_DIR = Path("~/repos/second-brain/knowledge_base").expanduser()
TEMPLATES_BASE_DIR = Path("~/repos/second-brain/templates").expanduser()

# Create the Typer app
app = typer.Typer(
    no_args_is_help=True,
    add_completion=False, # Optional: disable shell completion commands
    rich_markup_mode="markdown", # Use Markdown for help text styling
    help="A CLI tool to create knowledge base notes from templates."
)

@app.command(name="new", help="Create a new note from a template.")
def create_new_note():
    """
    Scans templates, prompts user for selection, handles daily logs,
    prompts for title (if needed), creates the file, and opens it.
    """
    available_templates = templates.scan_templates(TEMPLATES_BASE_DIR)
    if not available_templates:
        rprint("[bold red]Error:[/bold red] No templates found in {TEMPLATES_BASE_DIR}. Please create some templates.")
        raise typer.Exit(code=1)

    selected_template = templates.select_template(available_templates)
    if not selected_template:
        rprint("[yellow]Note creation cancelled.[/yellow]")
        raise typer.Exit()

    # --- Handle Daily Log ---
    if selected_template.type == "daily":
        target_path = file_utils.get_daily_log_path(KB_BASE_DIR)
        if target_path.exists():
            rprint(f"[cyan]Daily log for {target_path.stem} already exists. Opening...[/cyan]")
            file_utils.open_in_editor(target_path)
        else:
            rprint(f"[cyan]Creating daily log: {target_path.name}...[/cyan]")
            success = file_utils.create_note_from_template(
                template_path=selected_template.full_path,
                target_path=target_path,
                title=None # Title placeholder handled by create_note...
            )
            if success:
                rprint(f"[bold green]Success![/bold green] Created daily log: {target_path}")
                file_utils.open_in_editor(target_path)
            else:
                rprint("[bold red]Failed to create daily log.[/bold red]")
                raise typer.Exit(code=1)
        raise typer.Exit() # Daily log handled, exit cleanly

    # --- Handle Other Templates ---
    title = file_utils.prompt_for_title()
    if not title:
        rprint("[yellow]Note creation cancelled.[/yellow]")
        raise typer.Exit()

    filename = file_utils.sanitize_filename(title)
    target_dir = KB_BASE_DIR / selected_template.type
    target_path = target_dir / filename

    # Optional: Check if file already exists for non-daily notes
    if target_path.exists():
         rprint(f"[bold yellow]Warning:[/bold yellow] Note already exists: {target_path}")
         confirm_overwrite = inquirer.confirm(
             message="Overwrite existing note?",
             default=False,
         ).execute()
         if not confirm_overwrite:
             rprint("[yellow]Note creation cancelled.[/yellow]")
             raise typer.Exit()
         else:
             rprint(f"[yellow]Overwriting {target_path.name}...[/yellow]")


    rprint(f"[cyan]Creating note: {target_path.name} in {selected_template.type}...[/cyan]")
    success = file_utils.create_note_from_template(
        template_path=selected_template.full_path,
        target_path=target_path,
        title=title
    )

    if success:
        rprint(f"[bold green]Success![/bold green] Created note: {target_path}")
        file_utils.open_in_editor(target_path)
    else:
        rprint("[bold red]Failed to create note.[/bold red]")
        raise typer.Exit(code=1)

# --- Entry Point for `python -m scribe` ---
if __name__ == "__main__":
    app()
