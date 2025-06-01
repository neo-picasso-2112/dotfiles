# Installation Guide

## Quick Start (Recommended)

### Using pip with pyproject.toml
```bash
# Clone the repository
git clone https://github.com/neo-picasso-2112/dotfiles.git
cd dotfiles/custom_scripts/python/voice_assistant

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install -e .

# For development
pip install -e ".[dev]"
```

### Using requirements.txt (Alternative)
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install minimal dependencies
pip install -r requirements-minimal.txt

# OR install exact frozen dependencies
pip install -r requirements.txt
```

## Architecture-Specific Notes

### macOS Apple Silicon (M1/M2/M3)
If you encounter architecture issues:
```bash
# Install for ARM64
arch -arm64 pip install --no-cache-dir -r requirements-minimal.txt
```

### macOS Intel
If you encounter architecture issues:
```bash
# Install for x86_64
arch -x86_64 pip install --no-cache-dir -r requirements-minimal.txt
```

## Environment Setup

1. Set your Google API key:
```bash
export GOOGLE_API_KEY="your_api_key_here"

# Or create a .env file:
echo 'GOOGLE_API_KEY=your_api_key_here' > .env
```

2. Verify installation:
```bash
python -c "from RealtimeSTT import AudioToTextRecorder; print('✅ RealtimeSTT installed')"
python -c "import sounddevice; print('✅ Audio dependencies installed')"
```

## Troubleshooting

### NumPy Version Conflict
If you see NumPy-related errors:
```bash
pip uninstall numpy
pip install "numpy<2"
```

### PyAudio Installation Issues
On macOS, you might need:
```bash
brew install portaudio
pip install --no-cache-dir pyaudio
```

### Missing Dependencies
If imports fail:
```bash
pip install --force-reinstall -r requirements-minimal.txt
```

## Using UV (Alternative Package Manager)

UV can be used but has known issues with PyAudio on macOS:

```bash
# UV will create its own isolated environment
uv run main.py

# If you encounter PyAudio import errors, use the virtual environment method instead
```

**Known Issues with UV:**
- PyAudio may fail with `_PaMacCore_SetupChannelMap` symbol errors
- Architecture mismatches on Apple Silicon Macs
- UV creates separate environments that may conflict with system libraries

**Recommendation**: Use the virtual environment method for reliability.

## Verifying Installation

Run the test suite:
```bash
pytest tests/test_voice_transcriber.py tests/test_basic.py -v
```

All structural tests should pass (14 tests).