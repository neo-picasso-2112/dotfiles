# Voice Assistant - Speech-to-Text Feature

## Setup

1. Create virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
# or manually:
pip install google-genai sounddevice numpy RealtimeSTT rich PyAudio pytest "numpy<2"
```

3. Set your Google API key:
```bash
export GOOGLE_API_KEY=your_api_key_here
```

## Running the Application

### Option 1: Using Python directly (Recommended)
```bash
source .venv/bin/activate
python main.py
```

### Option 2: Using UV (may have architecture issues on some systems)
```bash
./main.py
```

## Usage

1. Run the application
2. Press Enter to start recording
3. Speak into your microphone
4. Watch real-time transcription appear as you speak
5. Press Enter again to stop recording
6. View the final transcription in a formatted panel
7. Press Ctrl+C to exit

## Testing

Run tests:
```bash
source .venv/bin/activate
pytest tests/test_voice_transcriber.py tests/test_basic.py -v
```

## Features

- Real-time speech-to-text transcription
- Live display of transcription as you speak
- Clean CLI interface with Rich formatting
- Uses Whisper tiny.en model for fast performance
- Previous TTS functionality preserved in comments for future integration

## Troubleshooting

- If you get "GOOGLE_API_KEY not set" error, make sure to export the environment variable
- For architecture issues with UV, use the virtual environment directly
- Ensure your microphone permissions are enabled for the terminal