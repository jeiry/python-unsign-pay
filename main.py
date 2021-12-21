import os
import cv2 as cv
import yaml
import aircv as ac
import requests
import threading
import re
import easyocr

reader = easyocr.Reader(['en'], gpu=False)

file = open("config.yaml", 'r', encoding="utf-8")
file_data = file.read()
file.close()
data = yaml.load(file_data, Loader=yaml.FullLoader)


def findLocation():
    threshold = 0.5
    try:
        imsch = ac.imread('search_mob.png')
        result = ac.find_all_template(ac.imread('screen.jpg'), imsch, threshold)
        return result
    except Exception as e:
        print('error', e)
        return None

def callback(fee,out_trade_no):
    payload = {
        'fee': fee,
        'out_trade_no':out_trade_no
    }
    r = requests.post("%spay/callback" % data['apiurl'], data=payload)
    print(r.json())
def noteMe():
    try:
        payload = {
        }
        r = requests.get("http://noteapi.yoyolife.fun/api/sms/task/exxxx08396/8", data=payload) #换成自己的id
        print(r.json())
    except Exception as e:
        print(e)

lastCheck = 0
loopCount = 0
if __name__ == '__main__':
    os.system("adb shell settings put system screen_brightness_mode 0")
    os.system("adb shell settings put system screen_brightness 0")
    while True:
        # 方法6
        os.system("adb shell input tap 484 133")
        os.system("adb exec-out screencap -p > screen.jpg")
        img = cv.imread('screen.jpg')
        try:
            loca = findLocation()

            if len(loca) > 0:

                obj = 0
                if len(loca) == 1:
                    obj = loca[-1]
                else:
                    for objSub in loca:
                        if objSub['result'][1] > 1000:
                            obj = objSub
                            break
                i = 0
                #
                if obj != None and obj['confidence'] > 0.95:
                    x = int(obj['result'][0])
                    y = int(obj['result'][1])
                    # print(x,y)
                    cv.rectangle(img, (x + 20, y + 230), (x + 590, y + 350), color=(0, 0, 255),
                                 thickness=2)
                    cv.rectangle(img, (x-140, y + 50), (x + 190, y + 110), color=(0, 0, 255),
                                 thickness=2)
                    imgPrice = img[y + 230:y + 350, x + 20:x + 590]
                    imgData = img[y + 50:y + 110, x -140:x + 190]
                    result = reader.readtext(imgPrice, detail=0)
                    num = re.sub("\D", "", result[-1])
                    resultData = reader.readtext(imgData, detail=0)
                    numID = re.sub("\D", "", resultData[-1])
                    numID = int(float(numID))

                    fee = int(float(num))
                    with open('last.log') as f:
                        lastCheck = f.read()
                        if lastCheck != '':
                            lastCheck = int(lastCheck)
                    if lastCheck != numID:
                        f = open("last.log", 'w')
                        f.write(str(numID))
                        f.close()
                        t = threading.Thread(target=callback, args=(fee,lastCheck,))
                        t.start()
                        print(i, fee,numID)
                    i += 1
            cv.imshow('result', img)
        except Exception as e:
            print(e)
        if loopCount >= 60:
            print('loopCount',loopCount)
            loopCount = 0
            t = threading.Thread(target=noteMe)
            t.start()
        else:
            loopCount += 1
        if ord("q") == cv.waitKey(1):
            break
