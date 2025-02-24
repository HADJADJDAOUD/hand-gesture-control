import cv2
import mediapipe as mp
import math

class handDetector():
    def __init__(self, mode=False, maxHands=2, detectionCon=0.7, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon
        
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.maxHands,
            min_detection_confidence=self.detectionCon,
            min_tracking_confidence=self.trackCon
        )
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]  # Landmark IDs for fingertips
        self.results = None
        self.handTypes = []  # To store Left/Right hand classification

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        self.handTypes = []  # Reset hand types for new frame
        
        if self.results.multi_hand_landmarks and self.results.multi_handedness:
            for idx, hand_handedness in enumerate(self.results.multi_handedness):
                hand_type = "Right" if hand_handedness.classification[0].label == "Right" else "Left"
                self.handTypes.append(hand_type)
                if draw:
                    handLms = self.results.multi_hand_landmarks[idx]
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
        
        return img

    def findPosition(self, img, handNo=0, draw=False):
        lmList = []
        bbox = []
        
        if self.results.multi_hand_landmarks and handNo < len(self.results.multi_hand_landmarks):
            myHand = self.results.multi_hand_landmarks[handNo]
            xList = []
            yList = []
            h, w, c = img.shape
            
            for id, lm in enumerate(myHand.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append([id, cx, cy])
                xList.append(cx)
                yList.append(cy)
                
                if draw:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
            
            if xList and yList:
                xmin, xmax = min(xList), max(xList)
                ymin, ymax = min(yList), max(yList)
                bbox = [xmin, ymin, xmax, ymax]
                
                if draw:
                    cv2.rectangle(img, (xmin - 20, ymin - 20), 
                                (xmax + 20, ymax + 20), (0, 255, 0), 2)
        
        return lmList, bbox

    def findDistance(self, p1, p2, img, handNo=0, draw=True):
        if not self.results.multi_hand_landmarks or handNo >= len(self.results.multi_hand_landmarks):
            return 0, img, []

        lmList, _ = self.findPosition(img, handNo, draw=False)
        if len(lmList) < max(p1, p2) + 1:
            return 0, img, []

        x1, y1 = lmList[p1][1], lmList[p1][2]
        x2, y2 = lmList[p2][1], lmList[p2][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        length = math.hypot(x2 - x1, y2 - y1)

        if draw:
            cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)
            if length < 30:  # Highlight when fingers are close
                cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)

        return length, img, [x1, y1, x2, y2, cx, cy]

    def getHandType(self, handNo=0):
        """Returns the type ('Left' or 'Right') of the specified hand."""
        if handNo < len(self.handTypes):
            return self.handTypes[handNo]
        return None

def main():
    import time
    pTime = 0
    cap = cv2.VideoCapture(0)
    detector = handDetector(maxHands=2)

    while True:
        success, img = cap.read()
        if not success:
            print("Failed to capture image")
            continue

        img = detector.findHands(img)
        num_hands = len(detector.handTypes) if detector.handTypes else 0
        
        for hand_idx in range(num_hands):
            lmList, bbox = detector.findPosition(img, handNo=hand_idx)
            if lmList:
                hand_type = detector.getHandType(hand_idx)
                print(f"Hand {hand_idx} ({hand_type}): Thumb tip at {lmList[4]}")

        cTime = time.time()
        fps = 1 / (cTime - pTime) if cTime - pTime != 0 else 0
        pTime = cTime

        cv2.putText(img, f'FPS: {int(fps)}', (10, 70), cv2.FONT_HERSHEY_PLAIN, 3,
                    (255, 0, 255), 3)

        cv2.imshow("Image", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()