import cv2
import time
import math
import numpy as np
import HandTrackingModule as htm
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc

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

# Initialize hand tracking module
detector = htm.handDetector()


volBar = 400
volPer = 0
brightBar = 400
brightPer = 0

while True:
    success, img = cap.read()
    if not success:
        continue

    img = detector.findHands(img)
    lmList, bbox = detector.findPosition(img, draw=False)
    num_hands = len(detector.handTypes) if detector.handTypes else 0

    for hand_idx in range(num_hands):
        handType = detector.handTypes[hand_idx]
        lmList, bbox = detector.findPosition(img, handNo=hand_idx, draw=False)
        
        if len(lmList) < 9:
            continue  

        x1, y1 = lmList[4][1], lmList[4][2]  # Thumb finger
        x2, y2 = lmList[8][1], lmList[8][2]  # other finger
        ## 
        length = math.hypot(x2 - x1, y2 - y1)
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        # Hand-specific controls
        if handType == "Left":
            # Volume Control you can change it though suuuuuuuuuuuuuuui
            vol = np.interp(length, [30, 200], [minVol, maxVol])
            volume.SetMasterVolumeLevel(vol, None)
            volPer = np.interp(length, [30, 200], [0, 100])
            volBar = np.interp(length, [30, 200], [400, 150])
        elif handType == "Right":
            # Brightness Control
            brightPer = np.interp(length, [30, 200], [0, 100])
            brightBar = np.interp(length, [30, 200], [400, 150])
            sbc.set_brightness(int(brightPer))

        # Draw fingers and connectors an3am ih
        cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
        cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)
        cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
        cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)
        if length < 30:
            cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)

    # Volume UI you can change colors but i like black 
    cv2.rectangle(img, (50, 150), (85, 400), (0, 0, 0), 3)
    cv2.rectangle(img, (50, int(volBar)), (85, 400), (0, 0, 0), cv2.FILLED)
    cv2.putText(img, f'Vol: {int(volPer)}%', (40, 450), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 3)

    # Brightness UI shining like you do suuuuuuuuuuui
    cv2.rectangle(img, (wCam - 100, 120), (wCam - 65, 400), (0, 0, 0), 3)
    cv2.rectangle(img, (wCam - 100, int(brightBar)), (wCam - 65, 400), (0, 0, 0), cv2.FILLED)
    cv2.putText(img, f'Bright: {int(brightPer)}%', (wCam - 180, 450), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 3)

    # FPS Display
    cTime = time.time()
    fps = 1 / (cTime - pTime) if (cTime - pTime) != 0 else 0
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 3)

    cv2.imshow("Image", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()