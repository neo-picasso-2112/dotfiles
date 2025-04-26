# scribe/main.py
import typer
# Removed Path import as constants are gone
from typing_extensions import Annotated
from rich import print as rprint
from InquirerPy import inquirer

# Use relative imports within the package
from scribe import config # <-- Import the new config module
from scribe.templates import select_template_nested
from scribe import file_utils

# --- Constants moved to config.py ---

# Create the Typer app
app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="markdown",
    help="A CLI tool to create knowledge base notes from templates."
)

@app.command(name="new", help="Create a new note from a template.")
def create_new_note():
    """
    Scans templates, prompts user for selection (nested), handles daily logs,
    prompts for title (if needed), creates the file, and opens it.
    """
    selected_template = select_template_nested() # This function now uses config internally

    if not selected_template:
        rprint("[yellow]Note creation cancelled or failed.[/yellow]")
        raise typer.Exit()

    # --- Handle Daily Log ---
    if selected_template.type == "daily":
        # *** Use config.DAILY_BASE_DIR ***
        target_path = file_utils.get_daily_log_path(config.DAILY_BASE_DIR)

        if target_path.exists():
            rprint(f"[cyan]Daily log for {target_path.stem} already exists. Opening...[/cyan]")
            file_utils.open_in_editor(target_path)
        else:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            rprint(f"[cyan]Creating daily log: {target_path.name}...[/cyan]")
            success = file_utils.create_note_from_template(
                template_path=selected_template.full_path,
                target_path=target_path,
                title=None
            )
            if success:
                rprint(f"[bold green]Success![/bold green] Created daily log: {target_path}")
                file_utils.open_in_editor(target_path)
            else:
                rprint("[bold red]Failed to create daily log.[/bold red]")
                raise typer.Exit(code=1)
        raise typer.Exit()

    # --- Handle Other Templates ---
    title = file_utils.prompt_for_title()
    if not title:
        rprint("[yellow]Note creation cancelled.[/yellow]")
        raise typer.Exit()

    filename = file_utils.sanitize_filename(title)
    # *** Use config.KB_BASE_DIR ***
    target_dir = config.KB_BASE_DIR / selected_template.type
    target_path = target_dir / filename

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
    target_path.parent.mkdir(parents=True, exist_ok=True)
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

# --- Entry Point ---
if __name__ == "__main__":
    app()
