import os
from pathlib import Path
from typing import List, NamedTuple, Optional
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

class TemplateInfo(NamedTuple):
    display_name: str
    full_path: Path
    type: str  # e.g., 'how-to', 'explanation', 'daily'

def scan_templates(templates_base_dir: Path) -> List[TemplateInfo]:
    """Scans the template directory for .md files."""
    templates = []
    if not templates_base_dir.is_dir():
        return [] # Return empty if base dir doesn't exist

    # Add Daily Log specifically
    daily_template_path = templates_base_dir / "daily" / "daily_log.md"
    if daily_template_path.exists():
         templates.append(TemplateInfo(
             display_name="Daily Log",
             full_path=daily_template_path,
             type="daily"
         ))

    for item in templates_base_dir.iterdir():
        if item.is_dir() and item.name != 'daily': # Skip daily as it's handled
            template_type = item.name
            for template_file in item.glob("*.md"):
                # Create a user-friendly name
                display = f"{template_type.capitalize()} / {template_file.stem.replace('_', ' ').title()}"
                templates.append(TemplateInfo(
                    display_name=display,
                    full_path=template_file,
                    type=template_type
                ))
    return templates

def select_template(templates: List[TemplateInfo]) -> Optional[TemplateInfo]:
    """Prompts the user to select a template."""
    if not templates:
        return None

    choices = [Choice(value=tpl.full_path, name=tpl.display_name) for tpl in templates]
    choices.sort(key=lambda choice: choice.name) # Sort alphabetically by display name

    try:
        selected_path = inquirer.select(
            message="Select a template to create a note:",
            choices=choices,
            vi_mode=True,
            mandatory=True,
        ).execute()

        # Find the full TemplateInfo object corresponding to the path
        return next((tpl for tpl in templates if tpl.full_path == selected_path), None)

    except KeyboardInterrupt:
        return None # User cancelled
