# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Codebase Overview

This repository contains two voice assistant implementations:
- **main.py**: Simple text-to-speech demo using Google Gemini AI
- **reference/main.py**: Full-featured voice assistant with speech recognition and text-to-speech

## Key Commands

### Running the Applications

```bash
# Run the simple TTS demo
./main.py

# Run the full voice assistant
./reference/main.py

# Voice assistant with conversation ID
./reference/main.py --id conversation123

# Voice assistant with initial prompt
./reference/main.py --prompt "Create a Python hello world script"
```

### Development Requirements

- Python 3.9+
- UV package manager (for dependency management)
- GOOGLE_API_KEY environment variable must be set

## Architecture

### Current Implementation (main.py)
- Uses inline UV script dependencies
- Generates content via Gemini AI and converts to speech
- Helper module provides audio playback utilities
- Audio format: 24kHz, mono, 16-bit PCM

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