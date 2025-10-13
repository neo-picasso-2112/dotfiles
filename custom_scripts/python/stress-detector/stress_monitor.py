#!/usr/bin/env python3
"""
Stress Monitor - Monitors your facial expressions and locks your Mac if you look stressed.
Runs completely locally using your webcam.
"""

import cv2
import time
import os
import subprocess
from fer import FER
import random

class StressMonitor:
    def __init__(self, check_interval=60, stress_threshold=0.3, consecutive_checks=2):
        """
        Initialize the stress monitor.

        Args:
            check_interval: Time in seconds between facial expression checks (default: 60)
            stress_threshold: Emotion threshold to consider stressed (default: 0.3)
            consecutive_checks: Number of consecutive stressed detections before locking (default: 2)
        """
        self.check_interval = check_interval
        self.stress_threshold = stress_threshold
        self.consecutive_checks = consecutive_checks
        self.stressed_count = 0

        # Initialize FER detector
        self.detector = FER(mtcnn=False)  # Use faster haar cascade instead of MTCNN

        # Motivational messages
        self.break_messages = [
            "YOU LOOK LIKE GARBAGE 🚨\nBro, I saw that face! Stop pretending productivity.\nYou're about to have a breakdown and you know it.\n\nGo for a 10-minute walk. It's OK. Your brain needs a restart.\nCome back as a better human. Please.",
            "INTERVENTION TIME! 🚨\nYour stress levels are off the charts.\nStep away from the screen NOW.\n\nTake a break. Touch grass. Breathe.",
            "MANDATORY BREAK INITIATED 🚨\nYour face says it all - you need a break.\nGo outside, stretch, or just close your eyes.\n\nYou'll thank me later.",
            "STRESS LEVEL: CRITICAL 🚨\nWork will still be there in 10 minutes.\nYour mental health won't if you keep this up.\n\nGo. Now. Walk.",
        ]

    def capture_face(self):
        """Capture a single frame from webcam and detect emotions."""
        print("📸 Capturing image from webcam...")

        # Initialize camera
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("❌ Error: Could not access webcam")
            return None

        # Give camera time to warm up
        time.sleep(0.5)

        # Capture frame
        ret, frame = cap.read()
        cap.release()

        if not ret:
            print("❌ Error: Could not capture frame")
            return None

        # Analyze emotions
        emotions = self.detector.detect_emotions(frame)

        return emotions

    def analyze_stress(self, emotions):
        """
        Analyze if the person is stressed based on detected emotions.
        Considers: angry, sad, fear as stress indicators.
        """
        if not emotions or len(emotions) == 0:
            print("⚠️  No face detected")
            return False, None

        # Get the first face detected
        face_emotions = emotions[0]['emotions']

        # Calculate stress score (angry + sad + fear + disgust)
        stress_score = (
            face_emotions.get('angry', 0) +
            face_emotions.get('sad', 0) +
            face_emotions.get('fear', 0) +
            face_emotions.get('disgust', 0)
        )

        # Get dominant emotion
        dominant_emotion = max(face_emotions.items(), key=lambda x: x[1])

        print(f"\n📊 Emotion Analysis:")
        print(f"   Dominant: {dominant_emotion[0]} ({dominant_emotion[1]:.2%})")
        print(f"   Stress Score: {stress_score:.2%}")
        for emotion, score in sorted(face_emotions.items(), key=lambda x: x[1], reverse=True):
            if score > 0.05:  # Only show emotions above 5%
                print(f"   - {emotion}: {score:.2%}")

        is_stressed = stress_score > self.stress_threshold
        return is_stressed, stress_score

    def lock_mac(self):
        """Lock the Mac screen."""
        print("🔒 Locking your Mac...")
        subprocess.run([
            "osascript",
            "-e",
            'tell application "System Events" to keystroke "q" using {control down, command down}'
        ])

    def show_notification(self, message):
        """Show macOS notification."""
        # Escape quotes in message for AppleScript
        safe_message = message.replace('"', '\\"').replace("'", "\\'")

        script = f'''
        display dialog "{safe_message}" buttons {{"OK, I'll take a break"}} default button 1 with title "🚨 STRESS DETECTED" with icon stop giving up after 5
        '''

        try:
            subprocess.run(["osascript", "-e", script], check=False, timeout=6)
        except:
            # If dialog times out or is dismissed, that's fine
            pass

    def run(self):
        """Main monitoring loop."""
        print("=" * 70)
        print("🧠 STRESS MONITOR ACTIVATED")
        print("=" * 70)
        print(f"⏱️  Checking your face every {self.check_interval} seconds")
        print(f"🎯 Stress threshold: {self.stress_threshold:.0%}")
        print(f"🔄 Required consecutive detections: {self.consecutive_checks}")
        print(f"💡 Press Ctrl+C to stop")
        print("=" * 70)
        print()

        try:
            while True:
                print(f"\n{'='*70}")
                print(f"⏰ Check time: {time.strftime('%I:%M:%S %p')}")
                print(f"{'='*70}")

                # Capture and analyze
                emotions = self.capture_face()

                if emotions is None:
                    print("⚠️  Skipping this check (could not capture image)")
                    time.sleep(self.check_interval)
                    continue

                is_stressed, stress_score = self.analyze_stress(emotions)

                if is_stressed:
                    self.stressed_count += 1
                    print(f"\n⚠️  STRESS DETECTED! Count: {self.stressed_count}/{self.consecutive_checks}")

                    if self.stressed_count >= self.consecutive_checks:
                        print(f"\n🚨 LOCKING SCREEN - You need a break!")

                        # Show notification
                        message = random.choice(self.break_messages)
                        self.show_notification(message)

                        # Lock the Mac
                        self.lock_mac()

                        # Reset counter
                        self.stressed_count = 0

                        # Give extra time after forced break
                        print(f"\n😌 Waiting {self.check_interval * 2} seconds after break...")
                        time.sleep(self.check_interval * 2)
                        continue
                else:
                    if self.stressed_count > 0:
                        print(f"✅ Stress levels normalized (was {self.stressed_count}/{self.consecutive_checks})")
                    else:
                        print("✅ You look fine! Keep it up!")
                    self.stressed_count = 0

                # Wait for next check
                print(f"\n😴 Sleeping for {self.check_interval} seconds...")
                print(f"   Next check at: {time.strftime('%I:%M:%S %p', time.localtime(time.time() + self.check_interval))}")
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print("\n\n👋 Stress monitor stopped. Take care of yourself!")
            print("=" * 70)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Monitor stress levels via facial expressions")
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Time in seconds between checks (default: 60)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.3,
        help="Stress threshold 0-1 (default: 0.3)"
    )
    parser.add_argument(
        "--checks",
        type=int,
        default=2,
        help="Consecutive stressed detections before locking (default: 2)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode - capture once and show emotions"
    )

    args = parser.parse_args()

    monitor = StressMonitor(
        check_interval=args.interval,
        stress_threshold=args.threshold,
        consecutive_checks=args.checks
    )

    if args.test:
        print("🧪 TEST MODE - Single capture")
        print("=" * 70)
        emotions = monitor.capture_face()
        if emotions:
            monitor.analyze_stress(emotions)
        print("\n✅ Test complete!")
    else:
        monitor.run()


if __name__ == "__main__":
    main()
