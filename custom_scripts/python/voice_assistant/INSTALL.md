# Installation Guide

## Quick Start (Recommended - Using UV)

UV automatically handles dependencies and architecture compatibility:

```bash
# Clone the repository
git clone https://github.com/neo-picasso-2112/dotfiles.git
cd dotfiles/custom_scripts/python/voice_assistant

# Install UV if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run the application (UV handles everything)
uv run main.py

# Or make it executable
chmod +x main.py
./main.py
```

## Alternative: Manual Installation

If you prefer traditional pip installation:

### Using pip with pyproject.toml
```bash
# Create virtual environment with correct architecture
# For Apple Silicon:
arch -arm64 python3 -m venv .venv
# For Intel:
arch -x86_64 python3 -m venv .venv

source .venv/bin/activate
pip install -e .
```

### Using requirements.txt
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements-minimal.txt
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

## Why UV Works Best

UV is the recommended method because it:
- Automatically handles architecture compatibility (x86_64 vs ARM64)
- Manages dependencies in isolated environments
- Resolves PyAudio/PortAudio issues automatically
- Works consistently across different macOS versions
- No manual virtual environment setup required

## Verifying Installation

Run the test suite:
```bash
pytest tests/test_voice_transcriber.py tests/test_basic.py -v
```

All structural tests should pass (14 tests).