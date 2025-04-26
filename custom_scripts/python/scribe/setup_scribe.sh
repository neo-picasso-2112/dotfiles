#!/usr/bin/env bash

echo "--- Setting up scribe CLI tool ---"

# --- Get paths relative to THIS script's location ---
# SCRIPT_DIR is the directory containing this setup_scribe.sh script, which is the TOOL_ROOT_DIR
TOOL_ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
TOOL_NAME="scribe" # Tool name is fixed here
# Define the virtual environment path INSIDE the tool directory
VENV_PATH="$TOOL_ROOT_DIR/.venv_$TOOL_NAME"
# Define the target bin directory (still user's global bin)
USER_BIN_DIR="$HOME/bin"
# Define the source and target for the symlink
SOURCE_EXECUTABLE="$TOOL_ROOT_DIR/bin/$TOOL_NAME" # Wrapper script inside tool dir
TARGET_EXECUTABLE="$USER_BIN_DIR/$TOOL_NAME"
REQ_FILE="$TOOL_ROOT_DIR/requirements.txt"
POETRY_FILE="$TOOL_ROOT_DIR/pyproject.toml"

# --- Common Setup ---

# 1. Ensure ~/bin exists
if [ ! -d "$USER_BIN_DIR" ]; then
    echo "Creating directory: $USER_BIN_DIR"
    mkdir -p "$USER_BIN_DIR"
fi

# 2. Check if ~/bin is in PATH
if [[ ":$PATH:" != *":$USER_BIN_DIR:"* ]]; then
    echo ""
    echo "[WARNING] Your PATH does not seem to include $USER_BIN_DIR."
    echo "Please add it to your shell configuration file (e.g., ~/.bashrc, ~/.zshrc):"
    echo "  export PATH=\"\$HOME/bin:\$PATH\""
    echo "You may need to restart your shell or run 'source ~/.your_shell_rc' for changes to take effect."
    echo ""
fi

# --- Scribe Specific Setup ---

# Check if wrapper script exists (sanity check)
if [ ! -f "$SOURCE_EXECUTABLE" ]; then
    echo "[ERROR] Wrapper script not found at $SOURCE_EXECUTABLE. Cannot set up scribe." >&2
    exit 1
fi

# 3. Create/Update Virtual Environment
echo "Setting up Python virtual environment at $VENV_PATH..."
if ! python3 -m venv "$VENV_PATH"; then
    echo "[ERROR] Failed to create Python virtual environment for scribe." >&2
    exit 1
fi

# 4. Install dependencies
echo "Installing dependencies for scribe..."
# Activate the specific venv
source "$VENV_PATH/bin/activate"
# Store current directory and cd into tool dir (which is TOOL_ROOT_DIR)
ORIGINAL_DIR=$(pwd)
cd "$TOOL_ROOT_DIR" || { echo "[ERROR] Failed to cd into $TOOL_ROOT_DIR." >&2; deactivate; exit 1; }

if [ -f "$POETRY_FILE" ]; then
    echo "Using poetry..."
    if ! command -v poetry &> /dev/null; then
         echo "[ERROR] poetry command not found, but pyproject.toml exists. Please install poetry." >&2
    elif ! poetry install --no-root --no-dev; then # Assumes tool is run via wrapper, not installed itself
         echo "[ERROR] poetry install failed for scribe." >&2
    else
         echo "Scribe dependencies installed via poetry."
    fi
elif [ -f "$REQ_FILE" ]; then
     echo "Using pip..."
     if ! pip install -r "$REQ_FILE"; then
         echo "[ERROR] pip install failed for scribe." >&2
     else
          echo "Scribe dependencies installed via pip."
     fi
else
     echo "[WARNING] No dependency file (requirements.txt or pyproject.toml) found for scribe. Assuming no dependencies."
fi

# Go back to original directory and deactivate
cd "$ORIGINAL_DIR"
deactivate

# 5. Create Symlink
echo "Creating symbolic link: $TARGET_EXECUTABLE -> $SOURCE_EXECUTABLE"
# Ensure source wrapper is executable
chmod +x "$SOURCE_EXECUTABLE"
# Remove existing link/file if it exists, then create link
ln -sf "$SOURCE_EXECUTABLE" "$TARGET_EXECUTABLE"

if [ $? -eq 0 ]; then
    echo "[SUCCESS] scribe setup complete!"
    echo "You should now be able to run the 'scribe' command (you might need to restart your shell)."
else
    echo "[ERROR] Failed to create symbolic link. Check permissions." >&2
    exit 1
fi

exit 0
