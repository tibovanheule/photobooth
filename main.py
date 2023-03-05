
import argparse
import base64
import time
import cv2
import numpy as np
import multiprocessing
from PIL import Image, ImageFont, ImageDraw
import requests

class booth():

    def cvText(self,text,loc,font=None):
        # Make into PIL Image
        im_p = Image.fromarray(self.state['frame'])
        # Get a drawing context
        draw = ImageDraw.Draw(im_p)
        if font is None:
            draw.text(loc,text,(255,255,255),font=self.salt)
        else:
            draw.text(loc,text,(255,255,255),font=font)
        # Convert back to OpenCV image and save
        self.state['frame'] = np.array(im_p)

    def save_frame(self,frame):
        fname =  str("booth/booth_"+str(int(time.time()))+'.png')
        cv2.imwrite(fname,frame)
        self.state['worklist'].append(fname)


    def normal(self):
        if self.state["Snap"]:
            display_time = self.state['countdown'] - int(time.time() - self.state['start_time'] )
            self.state['frame2'] = self.state['frame'].copy()
            if display_time > -1:
                self.cvText(str(display_time),(610-20,385-150))
            if display_time < 1:
                if not(self.state['Freeze']):
                    self.state['Freeze'] = True
                    self.state['Freeze_frame'] = self.state['frame2'].copy()
                    self.save_frame(self.state['frame2'])
                if self.state['Freeze']:
                    self.state['frame'] = self.state['Freeze_frame'].copy()
                    self.cvText("http://homekonvent.be/photobooth",(210-20,585-150),font=self.salt_smallest)
            if display_time < -1:
                self.state['Snap'] = False
                self.state['Freeze'] = False

    def quad_image(self,frame1,frame2,frame3,frame4):
        frame = np.zeros((720,1280,3),np.uint8)
        tmp_frame = cv2.resize(frame1,None,fx=0.5,fy=0.5)
        frame[0:360,0:640] = tmp_frame[0:360,0:640]
        tmp_frame = cv2.resize(frame2,None,fx=0.5,fy=0.5)
        frame[0:360,640:1280] = tmp_frame[0:360,0:640]
        tmp_frame = cv2.resize(frame3,None,fx=0.5,fy=0.5)
        frame[360:720,0:640] = tmp_frame[0:360,0:640]
        tmp_frame = cv2.resize(frame4,None,fx=0.5,fy=0.5)
        frame[360:720,640:1280] = tmp_frame[0:360,0:640]
        return frame

    def cartoon(self):
        num_down = 2
        num_bilateral = 7
        img_colour = self.state['frame']

        for _ in range(num_down):
            img_colour = cv2.pyrDown(img_colour)

        for _ in range(num_bilateral):
            img_colour = cv2.bilateralFilter(img_colour, d=9, sigmaColor=9, sigmaSpace=7)

        for _ in range(num_down):
            img_colour = cv2.pyrUp(img_colour)

        img_grey = cv2.cvtColor(self.state['frame'],cv2.COLOR_RGB2GRAY)
        img_blur = cv2.medianBlur(img_grey, 7)

        img_edge = cv2.adaptiveThreshold(img_blur, 255,
                                        cv2.ADAPTIVE_THRESH_MEAN_C,
                                        cv2.THRESH_BINARY,
                                        blockSize=9,
                                        C=2)
        img_edge = cv2.cvtColor(img_edge, cv2.COLOR_GRAY2RGB)
        self.state['frame'] = cv2.bitwise_and(img_colour, img_edge)
        if self.state['Snap']:
            self.normal()

    def four_col(self):
        tmp_frame = cv2.resize(self.state['frame'],None,fx=0.5,fy=0.5)
        tmp_grey = cv2.cvtColor(tmp_frame, cv2.COLOR_RGB2GRAY)
        tmp_invert = cv2.bitwise_not(tmp_grey)
        tmp_zeros = np.zeros((360,640),np.uint8)

        tmp_frame1 = np.zeros((360,640,3),np.uint8)
        tmp_frame2 = tmp_frame1.copy()
        tmp_frame3 = tmp_frame1.copy()
        tmp_frame4 = tmp_frame1.copy()

        tmp_frame1[0:360,0:640,0] = tmp_invert
        tmp_frame1[0:360,0:640,1] = tmp_grey
        tmp_frame1[0:360,0:640,2] = tmp_zeros

        tmp_frame2[0:360,0:640,1] = tmp_invert
        tmp_frame2[0:360,0:640,2] = tmp_grey
        tmp_frame2[0:360,0:640,0] = tmp_grey

        tmp_frame3[0:360,0:640,1] = tmp_invert
        tmp_frame3[0:360,0:640,0] = tmp_grey
        tmp_frame3[0:360,0:640,2] = tmp_invert

        tmp_frame4[0:360,0:640,2] = tmp_invert
        tmp_frame4[0:360,0:640,0] = tmp_grey
        tmp_frame4[0:360,0:640,1] = tmp_grey

        self.state['frame'][0:360,0:640] = tmp_frame1[0:360,0:640]
        self.state['frame'][0:360,640:1280] = tmp_frame2[0:360,0:640]
        self.state['frame'][360:720,0:640] = tmp_frame3[0:360,0:640]
        self.state['frame'][360:720,640:1280] = tmp_frame4[0:360,0:640]

        if self.state['Snap']:
            self.normal()

    def sepia(self):
        frame = self.state['frame'].copy()
        m_sepia = np.asarray([[0.272, 0.534, 0.131],
                                [0.349, 0.686, 0.168],
                                [0.393, 0.769, 0.189]])
        self.state['frame'] = cv2.transform(frame, m_sepia)
        if self.state['Snap']:
            self.normal()

    def grey(self):
        img_grey = cv2.cvtColor(self.state['frame'],cv2.COLOR_RGB2GRAY)
        self.state['frame'] = cv2.cvtColor(img_grey,cv2.COLOR_GRAY2RGB)
        if self.state['Snap']:
            self.normal()

    def __init__(self, id) -> None:
        self.state = {'Snap': False,
                "Freeze": False,
                "countdown": 5,
                "mode": 0,
                'frame_no': 1,
                'path':"."}
        #load_config(state)
        m = multiprocessing.Manager()
        self.worklist = m.list()
        p = multiprocessing.Process(target = other_process,args=(self.worklist,))
        p.start()
        self.state['worklist'] = self.worklist
        filters = [self.normal,self.cartoon,self.four_col,self.sepia,self.grey]
        cap = cv2.VideoCapture(id)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT,720)
        ret = 1
        self.salt = ImageFont.truetype("salt.ttf",150)
        self.salt_smallest = ImageFont.truetype("salt.ttf",50)
        salt = ImageFont.truetype("salt.ttf",100)
        while ret:
            ret, self.state['frame'] = cap.read()
            filters[self.state['mode']]()
            cv2.namedWindow("PhotoBooth", cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty("PhotoBooth", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            if not(self.state['Snap']):
                # Make into PIL Image
                im_p = Image.fromarray(self.state['frame'])
                # Get a drawing context
                draw = ImageDraw.Draw(im_p)
                
                draw.text((610-200,385-100),"Take a picture",(255,255,255),font=salt)
                with Image.open("arrow.png") as im:
                    im.thumbnail((128*2,128*2), Image.Resampling.LANCZOS)
                    im_p.paste(im,(150,300),mask=im)
                # Convert back to OpenCV image and save
                self.state['frame'] = np.array(im_p)
            cv2.imshow('PhotoBooth',self.state['frame'])
            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                break
            if not(self.state['Snap']):
                if key == ord(' '):
                    self.state['Snap'] = True
                    self.state['start_time'] = time.time()
                if key == ord('1'):
                    self.state['mode'] = 0
                if key == ord('2'):
                    self.state['mode'] = 1
                if key == ord('3'):
                    self.state['mode'] = 2
                if key == ord('4'):
                    self.state['mode'] = 3
                if key == ord('5'):
                    self.state['mode'] = 4
        cap.release()
        cv2.destroyAllWindows()
        while len(self.worklist) > 0:
            print('Sleeping main')
            time.sleep(1)
        self.worklist.append("QUIT")
        p.join()

def returnCameraIndexes():
    # checks the first 10 indexes.
    index = 0
    arr = []
    i = 10
    while i > 0:
        try:
            cap = cv2.VideoCapture(index)
            if cap.read()[0]:
                arr.append(index)
                cap.release()
            index += 1
            i -= 1
        except IndexError as e:
            return arr
    return arr

def other_process(worklist):
    sleep_timer = 0
    while 'QUIT' not in worklist:
        if len(worklist) > 0:
            fname = worklist.pop()
            print ('Uploading:',(fname))
            #UPLOAD
            img = cv2.imread(fname)
            jpg_img = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            b64_string = base64.b64encode(jpg_img[1]).decode('utf-8')
            requests.post("http://localhost:3356/image",json={"image":b64_string})
        else:
            time.sleep(1)
            sleep_timer += 1
            #if sleep_timer > 10000:
            #    login_google(state)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                        prog = 'Photobooth',
                        description = 'photobooth',
                        epilog = ' give camera index using -c flag')

    parser.add_argument('-c',"--camera")

    args = parser.parse_args()
    if args.camera is not None:
        booth(int(args.camera))
    else:
        print(returnCameraIndexes())
