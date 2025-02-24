import cv2
import time
import numpy as np
import HandTrackingModule as htm
import math
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

wCam, hCam = 1280, 720
cap =cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
pTime=0

#######################
###################

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = interface.QueryInterface(IAudioEndpointVolume)

volume.GetMasterVolumeLevel()
volRange=volume.GetVolumeRange()

#######################
minVol=volRange[0]
maxVol=volRange[1]
vol=0

detector = htm.handDetector()
while True:
    success, img = cap.read()
    img=detector.findHands(img)  
    
    
    lmList=detector.findPosition (img,draw=False)
    if (lmList) !=0:
        
        x1,y1=lmList[0][4][1],lmList[0][4][2]
        x2,y2=lmList[0][8][1],lmList[0][8][2]
        # x3,y3=lmList[0][12][1],lmList[0][12][2]
        # x4,y4=lmList[0][16][1],lmList[0][16][2]
        # x5,y5=lmList[0][20][1],lmList[0][20][2]
        
        
        cv2.circle(img,(x1,y1),5,(0,0,255),cv2.FILLED)
        cv2.circle(img,(x2,y2),5,(255,0,0),cv2.FILLED)
        # cv2.circle(img,(x3,y3),10,(255,0,0),cv2.FILLED)
        # cv2.circle(img,(x4,y4),10,(255,0,0),cv2.FILLED)
        # cv2.circle(img,(x5,y5),10,(255,0,0),cv2.FILLED)
        
        
        #if you wanted to print the line between the two fingers
        # cv2.line(img,(x1,y1),(x2,y2),(0,0,0),3)
        #---------------------------------------
        
        cx,cy=(x1+x2)//2,(y1+y2)//2
        
        # if you wanted to print the circle in the middle of the two fingers
        #cv2.circle(img,(cx,cy),2,(0,255,0),cv2.FILLED)
        
        
        length=math.hypot(x2-x1,y2-y1)
        
        #hand range was from 30 to 300
        #volume range was from -96 to 0
        vol=np.interp(length,[30,200],[minVol,maxVol])
        volBar=np.interp(length,[30,200],[400,150])
        volPer=np.interp(length,[30,200],[0,100])
        print('this is vol',vol)
        volume.SetMasterVolumeLevel(vol, None)
       
        
        if(length)<30:
            cv2.circle(img,(cx,cy),5,(255,255,255),cv2.FILLED)
    cv2.rectangle(img,(50,150),(85,400),(0,0,0),3)
    cv2.rectangle(img,(50,int(volBar)),(85,400),(0,0,0),cv2.FILLED)
    cv2.putText(img,f'{int(volPer)}%',(40,450),cv2.FONT_HERSHEY_PLAIN,2,(0,0,0),3)
    
    cTime=time.time()
    fps=1/(cTime-pTime)
    pTime=cTime
    cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 3)
    cv2.imshow("Img", img)
    cv2.waitKey(1)
    