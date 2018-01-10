import numpy as np
import cv2
import time
import glob
import os
import sys
import signal


import argparse

parser = argparse.ArgumentParser(description='PunkVision - gethsl')

parser.add_argument('--source', '--input', default=None, help='source/input (out/0.jpg)')
#parser.add_argument('-cv', default=2, type=int, help='OpenCV version')
parser.add_argument('--size', default=None, type=int, nargs=2, help='size of image')
parser.add_argument('--buffer', default=10, type=int, help='destroy N images from camera')
parser.add_argument('-e', '--exposure', default=None, type=float, help='set camera exposure to N')

args = parser.parse_args()

_LDOWN, _LUP = None, None

if cv2.__version__[0] == "2":
    print ("OpenCV2")
    import cv2.cv as cv
    _LDOWN = cv.CV_EVENT_LBUTTONDOWN
    _LUP = cv.CV_EVENT_LBUTTONUP
elif cv2.__version__[0] == "3":
    print ("OpenCV3")
    import cv2 as cv
    _LDOWN = cv.EVENT_LBUTTONDOWN
    _LUP = cv.EVENT_LBUTTONUP
else:
    print ("Don't know what OpenCV version!")
    exit(3)

vargs = vars(args)
for k in vargs:
    if isinstance(vargs[k], list):
        setattr(args, k, tuple(vargs[k]))

args.source = [args.source]
avgs = []
mins = []
maxs = []

img = None

nar = lambda x: np.array(x)

def get_slice(start, end):
    im = cv2.cvtColor(img, cv2.COLOR_BGR2HLS)
    return im[start[1]:end[1],start[0]:end[0]]

spt, ept = None, None
minxy, maxxy = None, None


button_down = False

def on_mouse(event, x, y, flags, params):
    global spt; global ept
    global minxy; global maxxy
    global avgs; global mins; global maxs
    global button_down
    if event == _LDOWN:
        button_down = True
        spt = (x, y)
    elif event == _LUP:
        button_down = False
        ept = (x, y)
        minxy = (min([spt[0], ept[0]]), min([spt[1], ept[1]]))
        maxxy = (max([spt[0], ept[0]]), max([spt[1], ept[1]]))
        data = get_slice(minxy, maxxy)
        H, L, S = data[:,:,0], data[:,:,1], data[:,:,2]  
        na = np.average
        nmin = np.min
        nmax = np.max
        avg = [na(H), na(S), na(L)]
        _min = [nmin(H), nmin(S), nmin(L)]
        _max = [nmax(H), nmax(S), nmax(L)]
        
        avgs += [avg]
        mins += [_min]
        maxs += [_max]

        print_latest()
        print_info()

    if button_down:
        dispimg = img.copy()
        cv2.rectangle(dispimg, spt, (x, y), (0, 0, 255))
        cv2.imshow('real image', dispimg)
        k = cv2.waitKey(10)

def reset_vals():
    global minxy; global maxxy
    minxy, maxxy = None, None


def print_latest():
    global avgs; global mins; global maxs
    print ("")
    print ("Last Avgs: ",[np.average(nar(avgs)[-1,i]) for i in range(0, 3)])
    print ("Last Mins: ",[np.min(nar(mins)[-1,i]) for i in range(0, 3)])
    print ("Last Maxs: ",[np.max(nar(maxs)[-1,i]) for i in range(0, 3)])

def print_info():
    global minxy; global maxxy
    print ("")
    print ("On image {0} out of {1}".format(count, len(args.source)))
    print ("Number of measurements: {0}".format(len(avgs)))
    print ("Points: {0} to {1}".format(minxy, maxxy))

def print_end():
    global avgs; global mins; global maxs
    tavgs = np.array(avgs)
    tmins = np.array(mins)
    tmaxs = np.array(maxs)
    print ("")
    if 0 in tavgs.shape:
        print("not enough measurements!")
        return
    final_tavg = [np.average(tavgs[:,i]) for i in range(0, 3)]
    final_tmin = [np.min(tmins[:,i]) for i in range(0, 3)]
    final_tmax = [np.max(tmaxs[:,i]) for i in range(0, 3)]
    print ("Final Avgs: ",final_tavg)
    print ("Final Mins: ",final_tmin)
    print ("Final Maxs: ",final_tmax)
    print ("")
    print ("Paste this into your config:\n")
    print ("args.exposure = {0}".format(args.exposure))
    print ("args.H = ({0}, {1})".format(final_tmin[0], final_tmax[0]))
    print ("args.S = ({0}, {1})".format(final_tmin[1], final_tmax[1]))
    print ("args.L = ({0}, {1})".format(final_tmin[2], final_tmax[2]))


count = 0
cam = None

def update_im():
    global img
    if args.source[0].startswith("/dev/video"):
        global cam
        l_int = len(args.source[0]) - 1
        while l_int >= 0 and args.source[0][l_int].isdigit():
            l_int -= 1
        if count == 0:
            if args.exposure is not None:
                cmd = "v4l2-ctl -d {0} -c exposure_auto=1 -c exposure_absolute={1}".format(args.source[0], args.exposure)
                os.system(cmd)
                time.sleep(.125)

            cam = cv2.VideoCapture(int(args.source[0][l_int+1:]))

        for i in range(0, args.buffer):
            cam.read()

        print ("cam read")
        retval, img = cam.read()
    else:
        if count == 0:
            args.source = list(glob.glob(args.source[0]))

        img = cv2.imread(args.source[count])

do_l = True
while do_l:
    print ("loop start")
    update_im()
    if args.size is not None:
        img = cv2.resize(img, tuple(args.size))

    cv2.namedWindow('real image')
    cv2.setMouseCallback('real image', on_mouse, 0)
    cv2.imshow('real image', img)

    k = cv2.waitKey(0)

    # right arrow
    if k == 65363:
        count += 1
    #left arrow
    elif k == 65361:
        count -= 1
    #delete key
    elif k == 65288:
        del avgs[-1]
        del mins[-1]
        del maxs[-1]
    elif k == 10 or count >= len(args.source) or count < 0:
        cv2.destroyAllWindows()
        print_end()
        do_l = False
    else:
        print ("Don't know what key you pressed (code {0}). Here's a summary:".format(k))
        print_end()
        #do_l = False

    print_info()            
    print_end()

