
import argparse
import time
import cv2
import os
import numpy as np
import multiprocessing

class booth():

    def cvText(self,frame,text,loc,font,size):
        cv2.putText(frame, text,loc,font,size,(255,255,255,255),12,cv2.LINE_AA)
        cv2.putText(frame, text,loc,font,size,(0,0,0,0),4,cv2.LINE_AA)

    def save_frame(self,state,frame):
        fname = os.path.join(state['path'],'booth_'+str(int(time.time()))+'.png')
        cv2.imwrite(fname,frame)
        state['worklist'].append(fname)


    def normal(self,state):
        if state["Snap"]:
            display_time = state['countdown'] - int(time.time() - state['start_time'] )
            state['frame2'] = state['frame'].copy()
            if display_time > -1:
                self.cvText(state['frame'], str(display_time),(610,385),state['font'],3)
            if display_time < 1:
                if not(state['Freeze']):
                    state['Freeze'] = True
                    state['Freeze_frame'] = state['frame2'].copy()
                    self.save_frame(state,state['frame2'])
                if state['Freeze']:
                    state['frame'] = state['Freeze_frame'].copy()
            if display_time < -1:
                state['Snap'] = False
                state['Freeze'] = False

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

    def cartoon(self,state):
        num_down = 2
        num_bilateral = 7
        img_colour = state['frame']

        for _ in range(num_down):
            img_colour = cv2.pyrDown(img_colour)

        for _ in range(num_bilateral):
            img_colour = cv2.bilateralFilter(img_colour, d=9, sigmaColor=9, sigmaSpace=7)

        for _ in range(num_down):
            img_colour = cv2.pyrUp(img_colour)

        img_grey = cv2.cvtColor(state['frame'],cv2.COLOR_RGB2GRAY)
        img_blur = cv2.medianBlur(img_grey, 7)

        img_edge = cv2.adaptiveThreshold(img_blur, 255,
                                        cv2.ADAPTIVE_THRESH_MEAN_C,
                                        cv2.THRESH_BINARY,
                                        blockSize=9,
                                        C=2)
        img_edge = cv2.cvtColor(img_edge, cv2.COLOR_GRAY2RGB)
        state['frame'] = cv2.bitwise_and(img_colour, img_edge)
        if state['Snap']:
            self.normal(state)

    def four_col(self,state):
        tmp_frame = cv2.resize(state['frame'],None,fx=0.5,fy=0.5)
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

        state['frame'][0:360,0:640] = tmp_frame1[0:360,0:640]
        state['frame'][0:360,640:1280] = tmp_frame2[0:360,0:640]
        state['frame'][360:720,0:640] = tmp_frame3[0:360,0:640]
        state['frame'][360:720,640:1280] = tmp_frame4[0:360,0:640]

        if state['Snap']:
            self.normal(state)

    def sepia(self,state):
        frame = state['frame'].copy()
        m_sepia = np.asarray([[0.272, 0.534, 0.131],
                                [0.349, 0.686, 0.168],
                                [0.393, 0.769, 0.189]])
        state['frame'] = cv2.transform(frame, m_sepia)
        if state['Snap']:
            self.normal(state)

    def grey(self,state):
        img_grey = cv2.cvtColor(state['frame'],cv2.COLOR_RGB2GRAY)
        state['frame'] = cv2.cvtColor(img_grey,cv2.COLOR_GRAY2RGB)
        if state['Snap']:
            self.normal(state)

    def erode(self,state):
        kernel = np.ones((5,5),np.uint8)
        state['frame'] = cv2.erode(state['frame'],kernel,iterations =3)
        if state['Snap']:
            self.normal(state)




    def __init__(self, id) -> None:
        state = {'Snap': False,
                "Freeze": False,
                "countdown": 5,
                "mode": 0,
                'font': cv2.FONT_HERSHEY_SIMPLEX,
                'frame_no': 1,
                'path':"."}
        #load_config(state)
        m = multiprocessing.Manager()
        worklist = m.list()
        p = multiprocessing.Process(target = other_process,args=(worklist,))
        p.start()
        state['worklist'] = worklist
        filters = [self.normal,self.cartoon,self.four_col,self.sepia,self.grey,self.erode]
        cap = cv2.VideoCapture(id)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT,720)
        ret = 1
        while ret:
            ret, state['frame'] = cap.read()
            filters[state['mode']](state)
            cv2.namedWindow("PhotoBooth", cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty("PhotoBooth", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            cv2.imshow('PhotoBooth',state['frame'])
            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                break
            if not(state['Snap']):
                if key == ord(' '):
                    state['Snap'] = True
                    state['start_time'] = time.time()
                if key == ord('1'):
                    state['mode'] = 0
                if key == ord('2'):
                    state['mode'] = 1
                if key == ord('3'):
                    state['mode'] = 2
                if key == ord('4'):
                    state['mode'] = 3
                if key == ord('5'):
                    state['mode'] = 4
                if key == ord('6'):
                    state['mode'] = 5
        cap.release()
        cv2.destroyAllWindows()
        while len(worklist) > 0:
            print('Sleeping main')
            time.sleep(1)
        worklist.append("QUIT")
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
        else:
            print('sleeping')
            time.sleep(1)
            sleep_timer += 1
            #if sleep_timer > 10000:
            #    login_google(state)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                        prog = 'Pothobooth',
                        description = 'photobooth',
                        epilog = ' give camera index using -c flag')

    parser.add_argument('-c',"--camera")

    args = parser.parse_args()
    if args.camera is not None:
        booth(int(args.camera))
    else:
        print(returnCameraIndexes())
