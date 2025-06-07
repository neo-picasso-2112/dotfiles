# Voice Assistant - Speech-to-Text (STT)

This application provides real-time voice transcription using your computer's microphone and Apple's built-in speech recognition capabilities (on macOS).

## Setup

1.  **Create and Activate a Virtual Environment:**
    It's highly recommended to use a virtual environment.
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On macOS/Linux
    # .\.venv\Scripts\activate  # On Windows
    ```

2.  **Install Dependencies:**
    The project uses `pyproject.toml` to manage dependencies. You can install them using `pip` or `uv`.

    *   **Using `pip`:**
        ```bash
        pip install -e .
        ```
        This installs the project in editable mode along with its dependencies (`rich`, `SpeechRecognition`, `PyAudio`, `python-dotenv`, `google-genai`).

    *   **Using `uv` (alternative):**
        ```bash
        uv pip install -e .
        # Or, to sync based on pyproject.toml directly:
        # uv sync
        ```

3.  **macOS Specific: Install `portaudio`**
    `PyAudio` (a dependency for microphone access) on macOS often requires `portaudio`. If you encounter issues during `PyAudio` installation or when running the app, install `portaudio` using Homebrew:
    ```bash
    brew install portaudio
    ```
    Then, you might need to reinstall `PyAudio`:
    ```bash
    pip uninstall PyAudio
    pip install PyAudio --no-cache-dir
    ```

4.  **Set Your Google API Key (for future TTS functionality):**
    While the current STT functionality doesn't require it, the application is set up to potentially use Google GenAI for Text-to-Speech (TTS) in the future.
    Create a `.env` file in the project root with your key:
    ```
    GOOGLE_API_KEY=your_google_api_key_here
    ```
    Or set it as an environment variable:
    ```bash
    export GOOGLE_API_KEY=your_google_api_key_here
    ```

## Running the Application

Ensure your virtual environment is activated.

### Method 1: Using `uv run` (Recommended if `uv` is installed)
`uv` can run the script and manage its execution environment based on the `/// script` header in `main.py` or `pyproject.toml`.
```bash
# If you haven't set GOOGLE_API_KEY in a .env file:
# export GOOGLE_API_KEY=your_google_api_key_here

uv run ./main.py
```

### Method 2: Using Python Directly
```bash
# If you haven't set GOOGLE_API_KEY in a .env file:
# export GOOGLE_API_KEY=your_google_api_key_here

python main.py
# Or, since main.py is executable:
# chmod +x main.py
# ./main.py
```

## Usage

1.  Run the application using one of the methods above.
2.  The application will initialize the speech recognizer.
3.  Press **Enter** when prompted to start speaking.
4.  Speak clearly into your microphone.
5.  The application will listen until it detects silence, then process your speech.
6.  The transcribed text will be displayed.
7.  Press **Ctrl+C** to exit the application.

## Testing

Test dependencies are defined in `pyproject.toml` (`pytest`, `pytest-asyncio`, `pytest-cov`).

1.  Ensure your virtual environment is activated and test dependencies are installed:
    ```bash
    pip install -e ".[test]"
    # or with uv
    # uv pip install -e ".[test]"
    ```
2.  Run tests:
    ```bash
    pytest -v
    ```
    This will discover and run tests in the `tests/` directory.

## Features

-   Real-time speech-to-text transcription using `SpeechRecognition` and Apple's native STT (on macOS).
-   Clean command-line interface (CLI) using the `rich` library.
-   Microphone input via `PyAudio`.
-   Setup for future Text-to-Speech (TTS) integration using `google-genai`.

## Troubleshooting

-   **`GOOGLE_API_KEY not set` error:** Ensure you have set the `GOOGLE_API_KEY` in a `.env` file or as an environment variable (required for the application to start, even if TTS is not yet fully implemented).
-   **Microphone Issues / `PyAudio` errors on macOS:**
    *   Ensure `portaudio` is installed (`brew install portaudio`).
    *   Try reinstalling `PyAudio` (`pip uninstall PyAudio; pip install PyAudio --no-cache-dir`).
    *   Make sure your terminal application has permission to access the microphone (System Settings > Privacy & Security > Microphone).
-   **"Could not understand audio" / No transcription:**
    *   Ensure your microphone is selected as the default input and is working.
    *   Speak clearly and in a relatively quiet environment.
    *   Check microphone volume levels.