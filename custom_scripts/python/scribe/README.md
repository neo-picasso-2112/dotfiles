# scribe

`scribe` is a personal command-line tool designed to quickly create new notes within a knowledge base located at `~/repos/second_brain/`. It utilizes predefined Markdown templates stored in `~/repos/second_brain/templates/` to ensure consistent note structure. This tool is managed as part of this dotfiles repository.

## Features

*   Interactive selection of note templates.
*   Special handling for daily notes (uses `YYYY-MM-DD.md` filename, opens if exists).
*   Prompts for note title for non-daily templates.
*   Automatically creates note files in the correct knowledge base subdirectory (e.g., `knowledge_base/how-to/`).
*   Populates template placeholders like `{{DATE}}`, `{{DATETIME}}`, `{{title}}`.
*   Opens the created or existing note in your default `$EDITOR`.

## Prerequisites

*   Python 3 (tested with 3.8+)
*   `pip` and the `venv` module (usually included with Python)
*   [Poetry](https://python-poetry.org/) (if using `pyproject.toml` for dependencies) or a `requirements.txt` file.
*   The target knowledge base directory structure must exist:
    *   `~/repos/second_brain/knowledge_base/`
    *   `~/repos/second_brain/templates/` (containing template subdirectories like `daily/`, `how-to/`, etc., with `.md` files inside)
*   The `~/bin` directory should be in your system's `$PATH`. The setup script checks for this and provides a warning if needed.

## Installation / Setup

This tool requires a one-time setup to create a dedicated virtual environment, install dependencies, and make the `scribe` command globally available via a symbolic link in `~/bin`.

1.  **Navigate** to this directory (`scribe`):
    ```bash
    cd ~/dotfiles/custom_scripts/python/scribe/
    ```

2.  **Make the setup script executable** (if needed):
    ```bash
    chmod +x setup_scribe.sh
    ```

3.  **Run the setup script**:
    ```bash
    ./setup_scribe.sh
    ```

The script will:
*   Create a virtual environment named `.venv_scribe` inside this directory.
*   Install Python dependencies listed in `pyproject.toml` (using Poetry) or `requirements.txt` (using pip) into the virtual environment.
*   Create a symbolic link from `~/bin/scribe` pointing to the executable wrapper script `bin/scribe` located within this directory.

*(If you encounter issues, check the output of the setup script for specific errors regarding dependency installation or permissions.)*

## Usage

Once set up successfully, simply run the command from anywhere in your terminal:

```bash
scribe
```

The tool will present an interactive prompt to select the desired note template. Follow the prompts to provide a title (if necessary), and the tool will create/open the note file for you in your $EDITOR.

## Configuration

Knowledge Base Location: The paths to your knowledge base (~/repos/second_brain/knowledge_base) and templates (~/repos/second_brain/templates) are currently hardcoded in scribe/main.py. Modify the KB_BASE_DIR and TEMPLATES_BASE_DIR variables in that file if your locations differ.
Templates: Add, remove, or modify Markdown templates (.md files) within the appropriate subdirectories of ~/repos/second_brain/templates/. The scribe tool dynamically discovers these templates at runtime (except for the specifically named daily/daily_log.md). Remember to place templates for different note types (e.g., 'how-to', 'explanation') in correspondingly named subdirectories.
Dependencies: Manage Python dependencies using the pyproject.toml (if using Poetry) or requirements.txt file within this directory. Rerun ./setup_scribe.sh after modifying dependencies to update the virtual environment.


