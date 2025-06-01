# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Codebase Overview

This repository contains two voice assistant implementations:
- **main.py**: Simple text-to-speech demo using Google Gemini AI
- **reference/main.py**: Full-featured voice assistant with speech recognition and text-to-speech

## Key Commands

### Running the Applications

```bash
# Run the Speech-to-Text voice transcriber
./main.py
# Press Enter to start recording, Enter again to stop
# Press Ctrl+C to exit

# Run the full voice assistant (reference implementation)
./reference/main.py

# Voice assistant with conversation ID
./reference/main.py --id conversation123

# Voice assistant with initial prompt
./reference/main.py --prompt "Create a Python hello world script"
```

### Running Tests

```bash
# Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install pytest rich numpy

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_voice_transcriber.py -v
```

### Development Requirements

- Python 3.9+
- UV package manager (for dependency management)
- GOOGLE_API_KEY environment variable must be set

## Architecture

### Current Implementation (main.py)
- Real-time Speech-to-Text using RealtimeSTT library
- Interactive CLI interface with rich formatting
- Continuous recording loop with Enter to start/stop
- Real-time transcription display during recording
- Uses Whisper model (tiny.en) for fast performance
- Previous TTS functionality commented out for future integration

### Reference Implementation (reference/main.py)
- Full voice interaction loop with trigger words ("goose", "cloud", "sonny")
- Async architecture for responsive audio streaming
- Integrates with external Goose CLI tool
- Persists conversations in YAML files
- Uses RealtimeSTT for speech recognition and Gemini for TTS

## Important Notes

- No test suite currently exists
- Dependencies are managed via UV inline script metadata
- The reference implementation requires Goose CLI to be installed separately
- Audio playback uses sounddevice library with specific PCM format requirements