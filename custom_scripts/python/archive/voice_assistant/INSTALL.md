# Installation Guide

This guide covers setting up the Voice Assistant application.

## Prerequisites

-   Python 3.9+
-   `git` (for cloning the repository)
-   On macOS, [Homebrew](https://brew.sh/) is recommended for installing `portaudio`.

## Installation Steps

1.  **Clone the Repository (if you haven't already):**
    ```bash
    git clone https://github.com/neo-picasso-2112/dotfiles.git
    cd dotfiles/custom_scripts/python/voice_assistant
    ```

2.  **Create and Activate a Virtual Environment:**
    This isolates project dependencies.
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On macOS/Linux
    # .\.venv\Scripts\activate  # On Windows
    ```

3.  **Install Dependencies:**
    The project uses `pyproject.toml` for dependency management.

    *   **Method 1: Using `uv` (Recommended)**
        `uv` is a fast Python package installer. If you don't have `uv`, install it:
        ```bash
        curl -LsSf https://astral.sh/uv/install.sh | sh
        # Or via pipx: pipx install uv
        ```
        Then, install dependencies:
        ```bash
        uv pip install -e .
        # This installs the project in editable mode and its dependencies.
        # Alternatively, `uv sync` can be used if you only want to install dependencies
        # specified in pyproject.toml and uv.lock without installing the project itself.
        ```

    *   **Method 2: Using `pip`**
        ```bash
        pip install -e .
        ```
        This installs the project in editable mode and its dependencies (`rich`, `SpeechRecognition`, `PyAudio`, `python-dotenv`, `google-genai`).

4.  **macOS Specific: Install `portaudio` for `PyAudio`**
    `PyAudio` is used for microphone access and on macOS, it often requires `portaudio`.
    ```bash
    brew install portaudio
    ```
    If `PyAudio` installation failed previously or you encounter runtime issues related to it, try reinstalling it after installing `portaudio`:
    ```bash
    pip uninstall PyAudio
    pip install PyAudio --no-cache-dir
    ```

5.  **Set Google API Key (for future TTS):**
    The application requires a Google API key to be set for potential future Text-to-Speech (TTS) functionality using Google GenAI.
    *   Create a `.env` file in the project root (`custom_scripts/python/voice_assistant/.env`):
        ```
        GOOGLE_API_KEY=your_google_api_key_here
        ```
    *   Or, set it as an environment variable:
        ```bash
        export GOOGLE_API_KEY="your_google_api_key_here"
        ```

## Running the Application
After installation and with the virtual environment activated:

*   **Using `uv run`:**
    ```bash
    uv run ./main.py
    ```
*   **Using Python directly:**
    ```bash
    python main.py
    # Or, make main.py executable:
    # chmod +x main.py
    # ./main.py
    ```
Refer to `README_STT.md` for detailed usage instructions.

## Troubleshooting

*   **`GOOGLE_API_KEY not set` error:**
    Ensure the `GOOGLE_API_KEY` is correctly set in your `.env` file or as an environment variable. The application checks for this key on startup.

*   **`PyAudio` or Microphone Issues on macOS:**
    *   Confirm `portaudio` is installed (`brew install portaudio`).
    *   Try reinstalling `PyAudio` as described in Step 4.
    *   Ensure your terminal application has microphone access permissions (System Settings > Privacy & Security > Microphone).

*   **"No module named 'X'" errors:**
    Make sure your virtual environment is activated and dependencies were installed correctly using `uv pip install -e .` or `pip install -e .`.

*   **Architecture issues on macOS (less common with `uv` or modern `pip`):**
    Modern Python and `pip`/`uv` usually handle Apple Silicon (ARM64) vs. Intel (x86_64) automatically. If you suspect an architecture mismatch with manually installed packages, ensure you are using a Python interpreter compiled for your Mac's architecture.

## Verifying Installation

1.  **Basic Dependency Check:**
    With your virtual environment activated:
    ```bash
    python -c "import rich; print('✅ rich installed')"
    python -c "import speech_recognition; print('✅ SpeechRecognition installed')"
    python -c "import pyaudio; print('✅ PyAudio installed')"
    ```

2.  **Run the Test Suite:**
    Install test dependencies if you haven't:
    ```bash
    pip install -e ".[test]"
    # or with uv:
    # uv pip install -e ".[test]"
    ```
    Then run pytest:
    ```bash
    pytest -v
    ```
    This will execute tests defined in the `tests/` directory.

## Why `uv` is a Good Choice
-   **Speed:** `uv` is significantly faster for installing and managing packages.
-   **Dependency Resolution:** Robust dependency resolution.
-   **`pyproject.toml` Native:** Works seamlessly with `pyproject.toml`.
-   **Lock Files:** Can use `uv.lock` for highly reproducible environments.
-   **Integrated Tools:** Combines functionalities of `pip`, `venv`, etc.
While `pip` is standard, `uv` offers a more modern and efficient experience for many Python development workflows.