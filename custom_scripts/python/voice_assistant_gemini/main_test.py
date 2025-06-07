#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "google-genai>=1.16.0",
#   "sounddevice",
#   "numpy",
# ]
# ///

"""
Test implementation using sounddevice with the exact same streaming
approach as the reference implementation
"""

import asyncio
import sys
import traceback
import sounddevice as sd
import numpy as np
from google import genai
from google.genai import types

if sys.version_info < (3, 11, 0):
    import taskgroup, exceptiongroup
    asyncio.TaskGroup = taskgroup.TaskGroup
    asyncio.ExceptionGroup = exceptiongroup.ExceptionGroup

CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

client = genai.Client()  # GOOGLE_API_KEY must be set as env variable

MODEL = "gemini-2.5-flash-preview-native-audio-dialog"
CONFIG = {
    "response_modalities": ["AUDIO"],
    "output_audio_transcription": {}
}


class AudioLoop:
    def __init__(self):
        self.audio_in_queue = None
        self.out_queue = None
        self.session = None
        self.input_stream = None
        self.output_stream = None

    async def listen_audio(self):
        """Capture audio continuously for proper VAD"""
        loop = asyncio.get_event_loop()
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Input status: {status}")
            # Convert float32 to int16 PCM bytes
            audio_bytes = (indata[:, 0] * 32767).astype(np.int16).tobytes()
            
            # Send all audio continuously for VAD
            try:
                asyncio.run_coroutine_threadsafe(
                    self.out_queue.put({"data": audio_bytes, "mime_type": "audio/pcm"}),
                    loop
                )
            except:
                pass  # Drop if queue is full
        
        self.input_stream = sd.InputStream(
            channels=CHANNELS,
            samplerate=SEND_SAMPLE_RATE,
            blocksize=CHUNK_SIZE,
            dtype='float32',
            callback=audio_callback
        )
        
        self.input_stream.start()
        while True:
            await asyncio.sleep(0.1)

    async def send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            await self.session.send_realtime_input(audio=msg)

    async def receive_audio(self):
        """Handle responses with real-time text streaming"""
        while True:
            turn = self.session.receive()
            turn_started = False
            
            async for response in turn:
                # Handle interruptions
                if hasattr(response, 'server_content') and response.server_content:
                    if hasattr(response.server_content, 'interrupted') and response.server_content.interrupted:
                        print("\n[Interrupted]")
                        # Clear any queued audio on interruption
                        while not self.audio_in_queue.empty():
                            self.audio_in_queue.get_nowait()
                        turn_started = False
                        continue
                    
                    # Stream transcription in real-time
                    if hasattr(response.server_content, 'output_transcription') and response.server_content.output_transcription:
                        if not turn_started:
                            print(f"\n[Gemini]: ", end="", flush=True)
                            turn_started = True
                        print(response.server_content.output_transcription.text, end="", flush=True)
                
                # Handle audio data
                if hasattr(response, 'data') and response.data:
                    self.audio_in_queue.put_nowait(response.data)

            # Clear audio queue at end of turn
            while not self.audio_in_queue.empty():
                self.audio_in_queue.get_nowait()

    async def play_audio(self):
        """Direct audio streaming for real-time playback"""
        # Create output stream with float32 for better quality
        self.output_stream = sd.OutputStream(
            channels=CHANNELS,
            samplerate=RECEIVE_SAMPLE_RATE,
            dtype='float32',  # Use float32 for better quality
            blocksize=256,    # Even smaller blocks for lower latency
            latency='low'     # Request low latency mode
        )
        
        self.output_stream.start()
        
        try:
            while True:
                # Get audio data from queue
                audio_data = await self.audio_in_queue.get()
                if audio_data:
                    # Convert int16 bytes to float32 for playback
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                    float_audio = audio_array.astype(np.float32) / 32768.0
                    # Write directly to stream
                    await asyncio.to_thread(self.output_stream.write, float_audio)
        except Exception as e:
            print(f"Playback error: {e}")
        finally:
            self.output_stream.stop()
            self.output_stream.close()

    async def run(self):
        print("🎙️  Starting Live API Native Audio Chat (sounddevice version)...")
        print("📡 Connecting to Gemini...")
        
        try:
            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session

                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)
                
                print("✅ Connected! Start speaking...")

                tg.create_task(self.send_realtime())
                tg.create_task(self.listen_audio())
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())
        except asyncio.CancelledError:
            print("\n👋 Chat ended")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            traceback.print_exc()
        finally:
            if self.input_stream:
                self.input_stream.stop()
                self.input_stream.close()
            if self.output_stream:
                self.output_stream.stop()
                self.output_stream.close()


if __name__ == "__main__":
    try:
        asyncio.run(AudioLoop().run())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")