# 🥁 AirPlay – Real-Time Gesture-Controlled Drum Kit

Play a virtual drum kit using just your hands and a webcam — no physical instruments required.  
AirDrum uses **computer vision** and **hand tracking** to detect drumming gestures in real time and play the corresponding drum sounds.

---

## 🎬 Demo

> Point your index finger at one of the four quadrants on screen and strike downward to play a drum!

| Quadrant | Drum |
|---|---|
| Top-Left | 🎩 Hi-Hat |
| Top-Right | 🦵 Kick Drum |
| Bottom-Left | 🔔 Cymbal |
| Bottom-Right | 🥁 Snare |

---

## 🛠️ How It Works

1. Your webcam feed is captured and processed frame-by-frame using **OpenCV**.
2. **MediaPipe Hands** tracks up to 2 hands and identifies 21 landmarks per hand.
3. The tip of your index finger (landmark 8) is used as the "drumstick".
4. A **depth-change algorithm** detects a forward striking motion by monitoring the Z-axis movement of the fingertip between frames.
5. When a strike is detected in a quadrant, **pygame** plays the corresponding drum sound.
6. A cooldown timer prevents repeated accidental triggers from a single gesture.

---

## 📦 Requirements

- Python 3.8+
- A working webcam

### Install dependencies

```bash
pip install opencv-python mediapipe pygame
```

---

## 📁 Project Structure

```
AirDrum/
│
├── Play.py           # Main application
│
├── snare.wav         # Snare drum sound
├── cymbal.wav        # Cymbal sound
├── kick.wav          # Kick drum sound
├── hihat.wav         # Hi-hat sound
│
├── snare.png         # Snare icon (transparent PNG)
├── cymbal.png        # Cymbal icon (transparent PNG)
├── kick.png          # Kick icon (transparent PNG)
└── hihat.png         # Hi-hat icon (transparent PNG)
```

> **Note:** The `.wav` and `.png` asset files are not included in this repository.  
> You can source free drum samples from [freesound.org](https://freesound.org) and create or download simple icons for each drum.

---

## ▶️ Running the App

```bash
python Play.py
```

- The app opens in **fullscreen** mode.
- Press **`q`** to quit.

---

## ⚙️ Configuration

You can tweak these variables at the top of `Play.py`:

| Variable | Default | Description |
|---|---|---|
| `cooldown` | `0.25` | Seconds between allowed hits on the same drum |
| `depth_threshold` | `0.025` | Sensitivity of the strike detection |
| `min_detection_confidence` | `0.7` | MediaPipe hand detection confidence |
| `min_tracking_confidence` | `0.7` | MediaPipe hand tracking confidence |

---

## 🧠 Tech Stack

| Technology | Role |
|---|---|
| [OpenCV](https://opencv.org/) | Webcam capture, frame rendering, visual overlays |
| [MediaPipe](https://mediapipe.dev/) | Real-time hand landmark tracking |
| [pygame](https://www.pygame.org/) | Low-latency audio playback |
| Python | Core application logic |

---

## 🚧 Known Limitations

- Works best in good lighting conditions.
- Accuracy may decrease if hands are partially out of frame.
- Z-depth from MediaPipe is a relative estimate, not true 3D depth — works well for strike detection but is sensitive to hand angle.

---

## 🤝 Contributing

Pull requests are welcome! Some ideas for improvement:
- Add more drum zones or customisable layouts
- Record and playback drum sessions
- Add a visual beat indicator / metronome
- Support MIDI output

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
