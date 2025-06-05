# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Codebase Overview

This repository contains two voice assistant implementations:
- **main.py**: Speech-to-Text (STT) demo using `SpeechRecognition` (Apple's STT on macOS) and setup for future Google Gemini AI Text-to-Speech (TTS).
- **reference/main.py**: Full-featured voice assistant with speech recognition and text-to-speech (older version).

## Key Commands

### Running the Applications

```bash
# Run the Speech-to-Text voice transcriber (main.py)
# Ensure GOOGLE_API_KEY is set (e.g., in .env file or exported)
# uv should handle dependencies if pyproject.toml is up to date.
uv run ./main.py
# Or if made executable:
# chmod +x main.py
# ./main.py

# Press Enter to start speaking. Stop speaking to finish.
# Press Ctrl+C to exit.

# Run the full voice assistant (reference implementation - may be outdated)
./reference/main.py

# Voice assistant with conversation ID
./reference/main.py --id conversation123

# Voice assistant with initial prompt
./reference/main.py --prompt "Create a Python hello world script"
```

### Running Tests

```bash
# Run tests (ensure virtual env is active and test dependencies installed)
# Install test dependencies:
# pip install -e ".[test]"
# or with uv:
# uv pip install -e ".[test]"

pytest -v
```

### Development Requirements

- Python 3.9+ (as per pyproject.toml, though main.py script header says >=3.9)
- A virtual environment manager (`venv`, `uv venv`)
- `pip` or `uv` for installing dependencies from `pyproject.toml`.
- `GOOGLE_API_KEY` environment variable must be set (for future TTS with Google GenAI).
- On macOS, `portaudio` (`brew install portaudio`) is needed for `PyAudio`.

## Architecture

### Current Implementation (main.py)
- Speech-to-Text (STT) using the `SpeechRecognition` library (utilizing Apple's native STT on macOS).
- Microphone input via `PyAudio`.
- Interactive Command Line Interface (CLI) with `rich` library for formatting.
- User presses Enter to start speaking; transcription occurs after silence.
- Setup for future Text-to-Speech (TTS) integration using `google-genai`.

### Reference Implementation (reference/main.py)
- Full voice interaction loop with trigger words ("goose", "cloud", "sonny")
- Async architecture for responsive audio streaming
- Integrates with external Goose CLI tool
- Persists conversations in YAML files
- Uses RealtimeSTT for speech recognition and Gemini for TTS

## Testing Architecture & Guidelines

### Key Testing Principles

**NEVER use excessive mocking.** When you need to mock imports at the module level, it's usually a sign that the code architecture needs improvement, not that you need better mocks.

### Critical Architectural Insight

**Problem**: Module-level imports of hardware dependencies (like `sounddevice`) make testing impossible.

**Solution**: Move hardware-dependent imports to runtime (inside method calls) rather than module-level.

**Example**:
```python
# ❌ BAD: Module-level import prevents testing
import sounddevice
class VoiceTranscriber:
    def __init__(self):
        # ...

# ✅ GOOD: Runtime import allows testing without hardware
class VoiceTranscriber:
    def __init__(self):
        import sounddevice  # Only imported when actually needed
        # ...
```

### Test Coverage Strategy

Our test suite focuses on **meaningful functionality** rather than artificial mocking:

- **18 comprehensive tests** covering core functionality
- **Mock only external dependencies** (hardware, network, UI)
- **Test actual business logic** and state management
- **Avoid testing mocked behavior** - if you're testing mocks, you're testing nothing

### Current Test Coverage (18 Tests)

- ✅ **Basic Infrastructure** (3 tests): Module imports, environment setup
- ✅ **Logging Infrastructure** (15 tests): Comprehensive logging validation
- ❌ **Core Business Logic** (0 tests): VoiceTranscriber class methods - **CRITICAL GAP**
- ❌ **Error Handling** (0 tests): Exception scenarios and recovery - **CRITICAL GAP**  
- ❌ **Main Application Loop** (0 tests): Async main function - **CRITICAL GAP**
- ❌ **Environment Validation** (0 tests): Missing API key handling - **CRITICAL GAP**

### Production Readiness: 30% 

**⚠️ NOT READY FOR PRODUCTION DEPLOYMENT**

See `PRODUCTION_TEST_ANALYSIS.md` for detailed gap analysis. Core application logic remains untested, presenting significant risk for production deployment.

**Minimum Required**: 40+ tests covering core business logic, error scenarios, and integration points before CI/CD deployment.

## Important Notes

- Core dependencies for `main.py` are managed via `pyproject.toml` (`SpeechRecognition`, `PyAudio`, `rich`, `python-dotenv`, `google-genai`).
- The `/// script` block in `main.py` also lists dependencies, primarily for `uv run`.
- The reference implementation (`reference/main.py`) might have different dependencies and setup.
- `GOOGLE_API_KEY` environment variable is required for `main.py` to start, anticipating future TTS integration.
- `PyAudio` on macOS requires `portaudio`.