import cv2 as cv
import mediapipe as mp
import pygame as py
import time

# ── MediaPipe setup ───────────────────────────────────────────────────────────
mp_hands = mp.solutions.hands          # Hand-tracking module
mp_draw = mp.solutions.drawing_utils   # Utility to draw hand landmarks (unused but available)

# ── Camera setup ──────────────────────────────────────────────────────────────
cap = cv.VideoCapture(0)   # Open the default webcam (index 0)

# ── Audio setup ───────────────────────────────────────────────────────────────
py.mixer.init()   # Initialise pygame's audio mixer

# Minimum seconds that must pass before the same drum can trigger again.
# Prevents a single gesture from firing the sound multiple times.
cooldown = 0.25

# Timestamps of the last time each drum was triggered
last_snare_time  = 0
last_cymbal_time = 0
last_kick_time   = 0
last_hihat_time  = 0

# Load drum sound files into pygame Sound objects
snare_sound  = py.mixer.Sound("snare.wav")
cymbal_sound = py.mixer.Sound("cymbal.wav")
kick_sound   = py.mixer.Sound("kick.wav")
hihat_sound  = py.mixer.Sound("hihat.wav")

# ── Icon images ───────────────────────────────────────────────────────────────
# Load drum icons with alpha channel (IMREAD_UNCHANGED preserves transparency)
snare_icon  = cv.imread("snare.png",  cv.IMREAD_UNCHANGED)
cymbal_icon = cv.imread("cymbal.png", cv.IMREAD_UNCHANGED)
kick_icon   = cv.imread("kick.png",   cv.IMREAD_UNCHANGED)
hihat_icon  = cv.imread("hihat.png",  cv.IMREAD_UNCHANGED)

# ── Depth-change threshold ────────────────────────────────────────────────────
# How much the Z-depth must increase in one frame to count as a "drum hit".
# MediaPipe Z values are relative; 0.025 was tuned empirically.
prev_depth_left  = None   # Previous frame's depth for the left hand
prev_depth_right = None   # Previous frame's depth for the right hand
depth_threshold  = 0.025

# ── Fullscreen window ─────────────────────────────────────────────────────────
cv.namedWindow("AirDrum", cv.WINDOW_NORMAL)
cv.setWindowProperty("AirDrum", cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)


# ── Helper: alpha-blend a PNG icon onto the camera frame ─────────────────────
def overlay_png(background, overlay, x, y, size=(120, 120)):
    """
    Draw a transparent PNG (overlay) onto background at pixel position (x, y).
    
    Parameters
    ----------
    background : np.ndarray  BGR frame from the webcam
    overlay    : np.ndarray  BGRA icon image
    x, y       : int         Top-left corner where the icon will be placed
    size       : tuple       (width, height) to resize the icon before drawing
    """
    overlay = cv.resize(overlay, size)
    h, w = overlay.shape[:2]

    # Safety check: icon must have an alpha channel
    if overlay.shape[2] < 4:
        return

    overlay_rgb   = overlay[:, :, :3]          # Colour channels
    overlay_alpha = overlay[:, :, 3] / 255.0   # Normalised alpha mask (0–1)

    # Safety check: icon must fit entirely within the frame
    if y + h > background.shape[0] or x + w > background.shape[1]:
        return

    # Region of interest on the background where the icon will land
    roi = background[y:y + h, x:x + w]

    # Blend each colour channel using: result = α * icon + (1−α) * background
    for c in range(3):
        roi[:, :, c] = (
            overlay_alpha * overlay_rgb[:, :, c] +
            (1 - overlay_alpha) * roi[:, :, c]
        )


# ── Main loop ─────────────────────────────────────────────────────────────────
with mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
) as hands:
    while True:
        success, frame = cap.read()
        if not success:
            break   # Stop if the webcam fails to deliver a frame

        # Mirror the frame so movements feel natural (like looking in a mirror)
        frame = cv.flip(frame, 1)

        # MediaPipe expects RGB; OpenCV uses BGR
        frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results   = hands.process(frame_rgb)

        # ── Draw the 2×2 grid that divides the screen into four drum zones ──
        # Horizontal divider at y=240
        cv.line(frame, (0, 240), (640, 240), (255, 255, 255), 2)
        # Vertical divider at x=320
        cv.line(frame, (320, 0), (320, 480), (255, 255, 255), 2)

        # ── Draw drum icons in each quadrant ─────────────────────────────────
        # Top-left     → Hi-hat
        overlay_png(frame, hihat_icon,  40,  40)
        # Top-right    → Kick drum
        overlay_png(frame, kick_icon,  440,  40)
        # Bottom-left  → Cymbal
        overlay_png(frame, cymbal_icon, 40, 280)
        # Bottom-right → Snare
        overlay_png(frame, snare_icon, 440, 280)

        current_time = time.time()

        # ── Hand tracking ─────────────────────────────────────────────────────
        if results.multi_hand_landmarks:
            for hand_no, hand_landmarks in enumerate(results.multi_hand_landmarks):

                # Determine which hand this is ("Left" or "Right")
                hand_label = results.multi_handedness[hand_no].classification[0].label

                h, w, c = frame.shape

                # Convert normalised landmark coords (0–1) to pixel coords,
                # and keep Z as-is (it's a relative depth estimate)
                landmarks = []
                for lm in hand_landmarks.landmark:
                    landmarks.append((int(lm.x * w), int(lm.y * h), lm.z))

                # Landmark 8 = tip of the index finger – used as the drum "stick"
                x, y  = landmarks[8][0], landmarks[8][1]
                depth = -landmarks[8][2]   # Negate so "closer to camera" → larger value

                # ── Calculate how much the finger moved toward the camera ────
                if hand_label == "Left":
                    if prev_depth_left is not None:
                        depth_change = depth - prev_depth_left
                    else:
                        depth_change = 0
                    prev_depth_left = depth
                else:
                    if prev_depth_right is not None:
                        depth_change = depth - prev_depth_right
                    else:
                        depth_change = 0
                    prev_depth_right = depth

                # ── Trigger drums based on zone + forward depth movement ──────
                # A hit is registered when:
                #   1. depth_change exceeds the threshold (finger moves forward)
                #   2. The index fingertip is inside the correct screen quadrant
                #   3. The cooldown period since the last hit has elapsed

                # Bottom-right quadrant → Snare
                if depth_change > depth_threshold and x > 320 and y > 240:
                    if current_time - last_snare_time > cooldown:
                        snare_sound.play()
                        last_snare_time = current_time
                        cv.rectangle(frame, (320, 240), (640, 480), (0, 165, 255), -1)  # Orange flash

                # Top-right quadrant → Kick drum
                if depth_change > depth_threshold and x > 320 and y < 240:
                    if current_time - last_kick_time > cooldown:
                        kick_sound.play()
                        last_kick_time = current_time
                        cv.rectangle(frame, (320, 0), (640, 240), (0, 165, 255), -1)    # Orange flash

                # Bottom-left quadrant → Cymbal
                if depth_change > depth_threshold and x < 320 and y > 240:
                    if current_time - last_cymbal_time > cooldown:
                        cymbal_sound.play()
                        last_cymbal_time = current_time
                        cv.rectangle(frame, (0, 240), (320, 480), (0, 165, 255), -1)    # Orange flash

                # Top-left quadrant → Hi-hat
                if depth_change > depth_threshold and x < 320 and y < 240:
                    if current_time - last_hihat_time > cooldown:
                        hihat_sound.play()
                        last_hihat_time = current_time
                        cv.rectangle(frame, (0, 0), (320, 240), (0, 165, 255), -1)      # Orange flash

                # ── Draw the fingertip cursor ─────────────────────────────────
                cv.circle(frame, (x, y), 10, (255, 255, 255), -1)   # White outer ring
                cv.circle(frame, (x, y),  8, (0,   0, 255), -1)    # Red inner dot

        # ── Display and exit ──────────────────────────────────────────────────
        cv.imshow("AirDrum", frame)
        if cv.waitKey(1) & 0xFF == ord('q'):   # Press 'q' to quit
            break

# ── Cleanup ───────────────────────────────────────────────────────────────────
cap.release()           # Release the webcam
cv.destroyAllWindows()  # Close all OpenCV windows
