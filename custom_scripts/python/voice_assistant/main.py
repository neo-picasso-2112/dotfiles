#!/usr/bin/env -S uv run --quiet --script

# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "google-genai>=1.16.0", # For future TTS
#   "rich>=13.0", # For rich text and UI elements
#   "python-dotenv>=1.0.0", # For GOOGLE_API_KEY
#   "SpeechRecognition>=3.8.1", # For speech-to-text
#   "PyAudio>=0.2.11",          # For microphone access with SpeechRecognition
# ]
# ///

"""
Voice Assistant with Real-time Speech-to-Text

This module provides real-time audio recording and transcription functionality
using RealtimeSTT. It records audio from the microphone and displays the
transcription in real-time.

Usage:
    ./main.py
    
    Press Enter to start recording, and Enter again to stop.
    Press Ctrl+C to exit.
"""

import os
# Set environment variables to suppress NumPy 2.x compatibility warnings
os.environ['NPY_DISABLE_COMPILE_WARNING'] = '1'
os.environ['DISABLE_PYCACHE'] = '1'

import speech_recognition as sr # Added for speech recognition
import sys
import asyncio
import time
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.align import Align
from rich.layout import Layout
from rich.rule import Rule
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize console for rich output
console = Console()

# ASCII Art for Voice Assistant
VOICE_ASSISTANT_LOGO = """
██    ██  ██████  ██  ██████ ███████ 
██    ██ ██    ██ ██ ██      ██      
██    ██ ██    ██ ██ ██      █████   
 ██  ██  ██    ██ ██ ██      ██      
  ████    ██████  ██  ██████ ███████ 

 █████  ███████ ███████ ██ ███████ ████████  █████  ███    ██ ████████ 
██   ██ ██      ██      ██ ██         ██    ██   ██ ████   ██    ██    
███████ ███████ ███████ ██ ███████    ██    ███████ ██ ██  ██    ██    
██   ██      ██      ██ ██      ██    ██    ██   ██ ██  ██ ██    ██    
██   ██ ███████ ███████ ██ ███████    ██    ██   ██ ██   ████    ██    
"""

def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

def show_welcome_screen():
    """Display the welcome screen with logo and instructions"""
    clear_screen()

    # Create the main welcome panel
    welcome_content = Text()
    welcome_content.append("Welcome to the ", style="white")
    welcome_content.append("Voice Assistant", style="bold #FF6B35")
    welcome_content.append(" research preview!", style="white")
 
    welcome_panel = Panel(
        Align.center(welcome_content),
        style="#FF6B35",
        padding=(0, 2)
    )
    
    # Display logo
    logo_panel = Panel(
        Align.center(Text(VOICE_ASSISTANT_LOGO, style="bold #FF6B35")),
        style="#FF6B35",
        padding=(1, 2)
    )
    
    # Status message
    status_text = Text()
    status_text.append("🎉 Login successful. Press ", style="cyan")
    status_text.append("Enter", style="bold white")
    status_text.append(" to continue", style="cyan")
    
    console.print(welcome_panel)
    console.print()
    console.print(logo_panel)
    console.print()
    console.print(Align.center(status_text))
    
    # Wait for user input
    input()

def show_interface_header():
    """Show the main interface header"""
    clear_screen()
    
    # Header with title
    header = Panel(
        Align.center(Text("🎙️ Voice Assistant STT", style="bold #FF6B35")),
        style="#FF6B35",
        padding=(0, 2)
    )
    console.print(header)
    console.print()
    
    # Instructions table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="#FF6B35")
    table.add_column(style="white")
    
    table.add_row("•", "Press Enter to start recording")
    table.add_row("•", "Stop speaking to finish recording")
    table.add_row("•", "Press Ctrl+C to exit")
    
    instruction_panel = Panel(
        table,
        title="Instructions",
        title_align="left",
        style="#FF6B35",
        padding=(1, 2)
    )
    
    console.print(instruction_panel)
    console.print()

# Will check for required environment variable in main() function

# Previous TTS code (commented out as requested)
"""
from google import genai
from google.genai import types as genai_types
from helper import play_audio

# Audio parameters (Gemini TTS typically outputs 24kHz, 16-bit PCM mono)
TTS_SAMPLE_RATE = 24000
TTS_CHANNELS = 1

# Configure the Gemini client with the API key
client = genai.Client(api_key=GOOGLE_API_KEY)

VOICE_NAME = "Sadaltager"
CONTENTS="Hi, please generate a short (like 100 words) transcript..."
MODEL_ID = "gemini-2.5-flash-preview-tts"

transcript = client.models.generate_content(
    model='gemini-2.5-flash-preview-05-20',
    contents=CONTENTS
  ).text

print(transcript)

response = client.models.generate_content(
  model=MODEL_ID,
  contents=transcript,
  config=genai_types.GenerateContentConfig(
    response_modalities=["AUDIO"],
    speech_config=genai_types.SpeechConfig(
        voice_config=genai_types.VoiceConfig(
            prebuilt_voice_config=genai_types.PrebuiltVoiceConfig(
                voice_name=VOICE_NAME,
            )
        )
    ),
  )
)

play_audio(response)
"""


class VoiceTranscriber:
    """Handles real-time audio recording and transcription using SpeechRecognition"""

    def __init__(self):
        """Initialize the voice transcriber with SpeechRecognition"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Initializing Speech Recognizer...", total=None)
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                with self.microphone as source:
                    console.print(Panel(
                        Text("🎙️  Adjusting for ambient noise, please wait...", style="yellow"),
                        style="yellow",
                        padding=(0, 2)
                    ))
                    # Listen for 1 second to adjust the energy threshold for ambient noise levels
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                progress.update(task, description="Speech Recognizer ready!")
                time.sleep(0.5)
                success_panel = Panel(
                    Text("✅ Voice Assistant ready! Press Enter to speak.", style="bold green"),
                    style="green",
                    padding=(0, 2)
                )
                console.print(success_panel)
                console.print()

            except Exception as e:
                progress.update(task, description="Error initializing Speech Recognizer!")
                error_message = f"Error initializing Speech Recognizer: {e}\n"
                error_message += "Please ensure you have a microphone and PyAudio installed correctly.\n"
                if sys.platform == "darwin": # macOS
                    error_message += "On macOS, you might need to install PortAudio: brew install portaudio\n"
                error_message += "Then try reinstalling PyAudio: pip uninstall PyAudio; pip install PyAudio"

                error_panel = Panel(
                    Text(error_message, style="bold red"),
                    style="red",
                    padding=(0, 2)
                )
                console.print(error_panel)
                sys.exit(1)
        
        self.current_text = ""
        self.is_recording = False

    def listen(self) -> str:
        """
        Record audio from the microphone and return the transcribed text.
        Uses SpeechRecognition library with Apple's Speech Recognition.
        
        Returns:
            str: The transcribed text from the audio, or an empty string on error/no speech.
        """
        self.is_recording = True
        self.current_text = ""

        recording_panel = Panel(
            Text("🎤 Listening... Speak now. Stop speaking to finish.", style="bold yellow"),
            style="yellow",
            padding=(0, 2)
        )
        console.print(recording_panel)

        try:
            with self.microphone as source:
                # recognizer.listen will stop automatically on silence
                audio = self.recognizer.listen(source)

            processing_panel = Panel(
                Text("🧠 Processing speech...", style="bold cyan"),
                style="cyan",
                padding=(0, 2)
            )
            console.print(processing_panel)

            try:
                # Recognize speech using Apple's built-in speech recognition
                self.current_text = self.recognizer.recognize_apple(audio)
                completion_panel = Panel(
                    Text("✅ Transcription complete!", style="bold green"),
                    style="green",
                    padding=(0, 2)
                )
                console.print(completion_panel)
                return self.current_text
            except sr.UnknownValueError:
                error_panel = Panel(
                    Text("⚠️ Could not understand audio", style="yellow"),
                    style="yellow",
                    padding=(0, 2)
                )
                console.print(error_panel)
                return ""
            except sr.RequestError as e:
                error_panel = Panel(
                    Text(f"⚠️ Apple Speech Recognition service error: {e}", style="bold red"),
                    style="red",
                    padding=(0, 2)
                )
                console.print(error_panel)
                return ""
        except sr.WaitTimeoutError:
            error_panel = Panel(
                Text("⚠️ No speech detected within the time limit.", style="yellow"),
                style="yellow",
                padding=(0,2)
            )
            console.print(error_panel)
            return ""
        except Exception as e:
            error_panel = Panel(
                Text(f"⚠️ An error occurred during listening: {e}", style="bold red"),
                style="red",
                padding=(0, 2)
            )
            console.print(error_panel)
            return ""
        finally:
            self.is_recording = False
    
    def shutdown(self):
        """Shutdown the transcriber and clean up resources"""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Shutting down transcriber...", total=None)
                # Console mode cleanup (minimal)
                self.current_text = ""
                self.is_recording = False
                progress.update(task, description="Transcriber shutdown complete")
                time.sleep(0.3)
        except Exception as e:
            error_panel = Panel(
                Text(f"Error during shutdown: {e}", style="bold red"),
                style="red",
                padding=(0, 2)
            )
            console.print(error_panel)


async def main():
    """Main application loop"""
    # Check for required environment variable (keeping for future TTS integration)
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        console.print("[bold red]Error: GOOGLE_API_KEY environment variable not set.[/bold red]")
        console.print("Please set it in your .env file or as an environment variable.")
        sys.exit(1)
    
    # Show welcome screen first
    show_welcome_screen()
    
    # Show main interface
    show_interface_header()
    
    # Initialize transcriber
    transcriber = VoiceTranscriber()
    
    try:
        while True:
            # Show prompt for user input
            prompt_panel = Panel(
                Text("Press Enter to start speaking", style="bold cyan"),
                style="cyan",
                padding=(0, 2)
            )
            console.print(prompt_panel)
            
            # Wait for user to press Enter
            input()
            
            # Record and transcribe
            transcription = transcriber.listen()
            
            if transcription:
                # Display the final transcription in a styled panel
                transcription_panel = Panel(
                    Text(transcription, style="white"),
                    title="📝 Transcription",
                    title_align="left",
                    style="#FF6B35",
                    padding=(1, 2)
                )
                console.print(transcription_panel)
            else:
                # Show no speech detected message
                no_speech_panel = Panel(
                    Text("No speech detected", style="yellow"),
                    style="yellow", 
                    padding=(0, 2)
                )
                console.print(no_speech_panel)
            
            console.print()  # Add spacing
            
    except KeyboardInterrupt:
        console.print()
        exit_panel = Panel(
            Text("Exiting Voice Assistant...", style="bold red"),
            style="red",
            padding=(0, 2)
        )
        console.print(exit_panel)
    finally:
        transcriber.shutdown()
        goodbye_panel = Panel(
            Text("Goodbye! 👋", style="bold cyan"),
            style="cyan",
            padding=(0, 2)
        )
        console.print(goodbye_panel)


if __name__ == "__main__":
    # Run the async main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
