# Stress Monitor 🧠

An AI-powered tool that monitors your facial expressions during work and locks your Mac when you look stressed, forcing you to take a break and touch grass.

## Features

- 📸 **Local Processing**: Everything runs on your Mac - no cloud, no data sent anywhere
- 🎯 **Smart Detection**: Uses facial emotion recognition to detect stress (anger, sadness, fear)
- 🔒 **Automatic Intervention**: Locks your screen when stress is detected
- 💬 **Motivational Messages**: Shows humorous yet caring notifications
- ⚙️ **Customizable**: Adjust check intervals, thresholds, and sensitivity

## How It Works

1. Captures a quick snapshot from your webcam every 60 seconds (configurable)
2. Analyzes your facial expression using AI emotion detection
3. Calculates a stress score based on negative emotions (angry, sad, fear, disgust)
4. After detecting stress in consecutive checks, locks your Mac and tells you to take a break
5. Shows a notification with a motivational (and slightly sassy) message

## Installation

### 1. Prerequisites

- Python 3.8 or higher
- macOS (for screen locking functionality)
- Built-in or external webcam

### 2. Install Dependencies

```bash
cd stress-detector
pip install -r requirements.txt
```

Or install manually:
```bash
pip install opencv-python fer numpy
```

### 3. Grant Camera Permissions

On first run, macOS will ask for camera permissions. Make sure to allow access in:
`System Settings > Privacy & Security > Camera`

## Usage

### Basic Usage

Run with default settings (checks every 60 seconds):

```bash
python stress_monitor.py
```

### Test Mode

Test your camera and see emotion detection in action:

```bash
python stress_monitor.py --test
```

### Custom Settings

```bash
# Check every 30 seconds
python stress_monitor.py --interval 30

# More sensitive detection (lower threshold = more sensitive)
python stress_monitor.py --threshold 0.2

# Require 3 consecutive detections before locking
python stress_monitor.py --checks 3

# Combine options
python stress_monitor.py --interval 45 --threshold 0.25 --checks 2
```

### Command Line Options

- `--interval SECONDS`: Time between checks (default: 60)
- `--threshold 0-1`: Stress threshold, lower = more sensitive (default: 0.3)
- `--checks NUMBER`: Consecutive stressed detections needed before locking (default: 2)
- `--test`: Run once to test camera and emotion detection

## How to Use During Work

### Option 1: Run in Terminal

Open a terminal and run:
```bash
cd /Users/williamnguyen/repos/stress-detector
python stress_monitor.py
```

Keep the terminal window open while you work.

### Option 2: Run in Background

```bash
cd /Users/williamnguyen/repos/stress-detector
nohup python stress_monitor.py > stress_monitor.log 2>&1 &
```

Check the log:
```bash
tail -f stress_monitor.log
```

Stop the background process:
```bash
pkill -f stress_monitor.py
```

### Option 3: Auto-start on Login (Advanced)

Create a LaunchAgent plist file for automatic startup.

## Understanding the Output

```
📊 Emotion Analysis:
   Dominant: neutral (45.23%)
   Stress Score: 32.45%
   - neutral: 45.23%
   - angry: 15.67%
   - sad: 12.34%
   - fear: 4.44%
```

- **Dominant**: The strongest detected emotion
- **Stress Score**: Combined score of negative emotions (angry + sad + fear + disgust)
- **Threshold**: If stress score exceeds threshold, it counts as "stressed"

## Customization

### Adjust Sensitivity

**Too many false positives** (locking too often)?
- Increase threshold: `--threshold 0.4`
- Increase required checks: `--checks 3`

**Not detecting stress** often enough?
- Decrease threshold: `--threshold 0.2`
- Decrease check interval: `--interval 30`

### Modify Messages

Edit the `break_messages` list in `stress_monitor.py` (line 32) to customize notifications.

## Privacy

- ✅ All processing happens locally on your Mac
- ✅ No images are saved or uploaded anywhere
- ✅ No data is sent to any external services
- ✅ Camera is only active for ~1 second during each check

## Troubleshooting

### Camera Not Working

1. Check camera permissions: `System Settings > Privacy & Security > Camera`
2. Close other apps using the camera (Zoom, Teams, etc.)
3. Test camera: `python stress_monitor.py --test`

### No Face Detected

- Make sure your face is visible and well-lit
- Sit closer to the camera
- Avoid backlighting (window behind you)

### Too Many False Positives

- Increase the stress threshold: `--threshold 0.4`
- Require more consecutive checks: `--checks 3`

### Screen Not Locking

- Check macOS version compatibility
- Test manually: Press `Control + Command + Q`

## Technical Details

- **Emotion Detection**: Uses FER (Facial Emotion Recognition) library
- **Face Detection**: Haar Cascade classifier (fast, no GPU needed)
- **Emotions Detected**: angry, sad, fear, happy, surprise, neutral, disgust
- **Stress Calculation**: Sum of angry + sad + fear + disgust scores

## Contributing

Feel free to modify and improve! Some ideas:

- Add logging to track stress patterns over time
- Create a menu bar app for easier control
- Add sound alerts
- Track "productivity score" vs break frequency
- Integration with calendar to avoid locking during meetings

## License

Do whatever you want with this code. Just promise me you'll actually take breaks when it tells you to.

## Disclaimer

This tool is meant to help promote healthy work habits. If you're experiencing chronic stress, please talk to a healthcare professional. This is a fun project, not medical advice.

---

Made with ❤️ (and a bit of tough love) for healthier work habits
