import cv2
import time
import math
import numpy as np
import HandTrackingModule as htm
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc
import sounddevice as sd
import queue
import json
from vosk import Model, KaldiRecognizer

# Initialize camera settings
wCam, hCam = 1280, 720
cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0

# Initialize volume control
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = interface.QueryInterface(IAudioEndpointVolume)
volRange = volume.GetVolumeRange()
minVol, maxVol = volRange[0], volRange[1]

# Initialize hand detector
detector = htm.handDetector(maxHands=2)

# Initialize brightness and volume parameters
volBar = 400
volPer = 0
brightBar = 400
brightPer = 0

# Load Vosk Speech Recognition Model
model = Model("vosk-model")  # Make sure this path is correct
recognizer = KaldiRecognizer(model, 16000)
mic_queue = queue.Queue()

# Voice control variables
control_active = False  # Flag to toggle hand control

# Function to process live audio
def callback(indata, frames, time, status):
    """Reads audio from the microphone and puts it in a queue."""
    if status:
        print(status, flush=True)
    mic_queue.put(bytes(indata))

def listen_for_commands():
    """Background thread to listen for voice commands."""
    global control_active
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16",
                           channels=1, callback=callback):
        print("Say 'start' to enable hand control or 'stop' to disable it.")
        while True:
            data = mic_queue.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                command = result.get("text", "").lower()
                if command:
                    print(f"Command heard: {command}")
                    if "start" in command:
                        control_active = True
                        print("Hand control activated.")
                    elif "stop" in command:
                        control_active = False
                        print("Hand control deactivated.")

# Start voice listener in a separate thread
import threading
voice_thread = threading.Thread(target=listen_for_commands, daemon=True)
voice_thread.start()

while True:
    success, img = cap.read()
    if not success:
        continue

    img = detector.findHands(img)
    lmList, bbox = detector.findPosition(img, draw=False)
    num_hands = len(detector.handTypes) if detector.handTypes else 0

    if control_active:  # Only process hand gestures if control is active
        for hand_idx in range(num_hands):
            handType = detector.handTypes[hand_idx]
            lmList, bbox = detector.findPosition(img, handNo=hand_idx, draw=False)
            
            if len(lmList) < 9:
                continue  # Skip if landmarks aren't detected properly

            x1, y1 = lmList[4][1], lmList[4][2]  # Thumb tip
            x2, y2 = lmList[8][1], lmList[8][2]  # Index finger tip
            length = math.hypot(x2 - x1, y2 - y1)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            # Hand-specific controls
            if handType == "Left":
                # Volume Control
                vol = np.interp(length, [30, 200], [minVol, maxVol])
                volume.SetMasterVolumeLevel(vol, None)
                volPer = np.interp(length, [30, 200], [0, 100])
                volBar = np.interp(length, [30, 200], [400, 150])
            elif handType == "Right":
                # Brightness Control
                brightPer = np.interp(length, [30, 200], [0, 100])
                brightBar = np.interp(length, [30, 200], [400, 150])
                sbc.set_brightness(int(brightPer))

            # Draw fingers and connectors
            cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)
            if length < 30:
                cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)

    # Volume UI
    cv2.rectangle(img, (50, 150), (85, 400), (0, 0, 0), 3)
    cv2.rectangle(img, (50, int(volBar)), (85, 400), (0, 0, 0), cv2.FILLED)
    cv2.putText(img, f'Vol: {int(volPer)}%', (40, 450), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 3)

    # Brightness UI
    cv2.rectangle(img, (wCam - 100, 150), (wCam - 65, 400), (0, 0, 0), 3)
    cv2.rectangle(img, (wCam - 100, int(brightBar)), (wCam - 65, 400), (0, 0, 0), cv2.FILLED)
    cv2.putText(img, f'Bright: {int(brightPer)}%', (wCam - 150, 450), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 3)

    # FPS and Control Status Display
    cTime = time.time()
    fps = 1 / (cTime - pTime) if (cTime - pTime) != 0 else 0
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 3)
    status_text = "Control: ON" if control_active else "Control: OFF"
    cv2.putText(img, status_text, (40, 80), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0) if control_active else (0, 0, 255), 3)

    cv2.imshow("Image", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
