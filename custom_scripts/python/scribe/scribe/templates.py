# scribe/templates.py
import os
from pathlib import Path
from typing import List, NamedTuple, Optional, Dict, Union
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich import print as rprint

from scribe import config # <-- Import the new config module

# Keep TemplateInfo the same
class TemplateInfo(NamedTuple):
    display_name: str
    full_path: Path # Need Path for this NamedTuple, so import it here now
    type: str
    template_name: str

# Renamed function for clarity - scans and groups templates
def scan_and_group_templates() -> Dict[str, List[TemplateInfo]]: # No longer needs argument
    """Scans the template directory and groups .md files by type."""
    templates_base_dir = config.TEMPLATES_BASE_DIR # <-- Use config value
    grouped_templates: Dict[str, List[TemplateInfo]] = {}

    if not templates_base_dir.is_dir():
        rprint(f"[bold red]Error:[/bold red] Templates directory not found: {templates_base_dir}")
        return grouped_templates

    # --- Handle Daily Log Separately ---
    daily_template_path = templates_base_dir / "daily" / "daily_log.md"
    if daily_template_path.is_file():
        grouped_templates["daily"] = [
            TemplateInfo(
                display_name="Daily Log",
                full_path=daily_template_path,
                type="daily",
                template_name="Daily Log"
            )
        ]
    else:
        rprint(f"[bold yellow]Warning:[/bold yellow] Daily log template not found at {daily_template_path}")


    # --- Handle Other Types ---
    for item in templates_base_dir.iterdir():
        if item.is_dir() and item.name != 'daily':
            template_type = item.name
            type_templates: List[TemplateInfo] = []
            for template_file in item.glob("*.md"):
                # Need Path here too
                from pathlib import Path # Import locally or at top if needed elsewhere
                template_name = template_file.stem.replace('_', ' ').replace('-', ' ').title()
                type_templates.append(TemplateInfo(
                    display_name=f"{template_type.capitalize()} / {template_name}",
                    full_path=template_file,
                    type=template_type,
                    template_name=template_name
                ))

            if type_templates:
                type_templates.sort(key=lambda tpl: tpl.template_name)
                grouped_templates[template_type] = type_templates

    return grouped_templates

# Rewritten selection function
def select_template_nested() -> Optional[TemplateInfo]:
    """Prompts user first for Type, then for specific Template."""

    # Call scan_and_group_templates without argument
    grouped_templates = scan_and_group_templates()

    if not grouped_templates:
        return None

    # --- First Prompt: Select Type ---
    available_types = sorted([key for key in grouped_templates.keys() if key != 'daily'])
    type_choices: List[Union[Choice, str]] = []

    if "daily" in grouped_templates:
        type_choices.append(Choice(value="daily", name="Daily Log"))

    type_choices.extend([Choice(value=t, name=t.replace('_', ' ').replace('-', ' ').title()) for t in available_types])

    if not type_choices:
        rprint("[bold red]Error:[/bold red] No template types with valid templates found.")
        return None

    try:
        selected_type = inquirer.select(
            message="Select the TYPE of note:",
            choices=type_choices,
            vi_mode=True,
            mandatory=True,
        ).execute()

    except KeyboardInterrupt:
        return None

    # --- Handle Selection ---
    if selected_type == "daily":
        return grouped_templates["daily"][0]

    # --- Second Prompt: Select Template within Type ---
    templates_of_type = grouped_templates.get(selected_type)

    if not templates_of_type:
        rprint(f"[bold red]Error:[/bold red] Could not find templates for selected type '{selected_type}'.")
        return None

    if len(templates_of_type) == 1:
        rprint(f"[cyan]Selecting only available template: {templates_of_type[0].template_name}[/cyan]")
        return templates_of_type[0]

    template_choices = [
        Choice(value=tpl.full_path, name=tpl.template_name)
        for tpl in templates_of_type
    ]

    try:
        selected_template_path = inquirer.select(
            message=f"Select TEMPLATE for '{selected_type.title()}':",
            choices=template_choices,
            vi_mode=True,
            mandatory=True,
        ).execute()

        final_selection = next((tpl for tpl in templates_of_type if tpl.full_path == selected_template_path), None)
        return final_selection

    except KeyboardInterrupt:
        return None
