# 🖐️ HandyCodes — Gesture-Controlled Code Editor

> A real-time hand gesture recognition system that lets you **write and execute Python code using only hand gestures** — no keyboard needed.

---

## Overview

HandyCodes uses **MediaPipe** for real-time hand landmark detection and maps specific hand gestures to Python code snippets. When a gesture is held for 0.3 seconds, the corresponding code is automatically inserted into a live code editor and executed — all through a custom-built **Tkinter GUI** with syntax highlighting and line numbers.

```
Webcam Feed
     ↓
MediaPipe Hand Landmark Detection (21 keypoints)
     ↓
Gesture Classification (finger extension logic)
     ↓
Code Generation → Live Editor → Auto-Execution
     ↓
Console Output
```

---

## ✋ Gesture → Code Mapping

| Gesture | Code Generated |
|---------|---------------|
| ✋ Open Palm | `print("Hello World")` |
| 👍 Thumbs Up | `x = 10` + print statement |
| ✌️ Victory | `if x > 5:` conditional block |
| ☝️ Pointing Index | `for i in range(5):` loop |
| ✊ Fist | Stop execution message |
| 🤟 Three Fingers | Function definition + call |

---

## Features

- **Real-time gesture detection** via webcam using MediaPipe (21 hand landmarks)
- **Live code editor** with syntax highlighting (strings, conditionals) and line numbers
- **Auto-execution** — gestures trigger code insertion and immediate execution
- **Console output panel** — see results instantly
- **Multi-camera support** — switch between available cameras
- **Pause/Resume** camera feed
- **Save code** to `.py` file with timestamp
- **0.3s hold time + 1s cooldown** to prevent accidental triggers

---

## Project Structure

```
hand-gesture-recognition/
├── src/
│   └── handycodes_v8.py     # Main application (latest version)
├── README.md                 # This file
├── requirements.txt          # Dependencies
└── .gitignore
```

---

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/sam-priti/hand-gesture-recognition.git
cd hand-gesture-recognition
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run
```bash
python src/handycodes_v8.py
```

> ⚠️ Make sure your webcam is connected. Press **Q** to quit the camera window.

---

## How It Works

### Hand Landmark Detection
MediaPipe detects **21 hand landmarks** per frame. Finger extension is determined by comparing tip vs. PIP joint Y-coordinates:
```python
index_extended = index_tip_y < index_pip_y  # Tip above PIP = extended
```

### Gesture Classification
Counts extended fingers and maps combinations to gestures:
- 5 fingers → Open Palm
- 0 fingers → Fist
- Index only → Pointing
- Index + Middle → Victory
- Thumb only → Thumbs Up
- 3 fingers → Three Fingers

### Gesture Stability
- **Hold time:** 0.3s — must hold gesture before triggering
- **Cooldown:** 1.0s — prevents repeated triggers

---

## Requirements

- Python 3.8+
- Webcam

---

## Author

**Sampriti Mohanty** | Woxsen University, Hyderabad
**Shreyansh Gaur** | Woxsen University, Hyderabad
**Tanishq Katoch** | Woxsen University, Hyderabad




