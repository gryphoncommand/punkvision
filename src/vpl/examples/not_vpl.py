"""

Non VPL simple camera viewer

"""

import cv2
import argparse
import time

parser = argparse.ArgumentParser(description='webcam viewer')

parser.add_argument("source", nargs='?', default=0, type=int, help='camera source (can be video file)')

parser.add_argument("-s", "--size", default=None, type=int, nargs=2, help='size')
parser.add_argument("-np", "--no-prop", action='store_true', help='use this flag to not use CameraProperties')
parser.add_argument("-ns", "--no-show", action='store_true', help='use this flag to not show the image')

args = parser.parse_args()


src = cv2.VideoCapture(args.source)

# set preferred width and height
if args.size is not None and not args.no_prop:
    src.set(cv2.CAP_PROP_FRAME_WIDTH, args.size[0]) 
    src.set(cv2.CAP_PROP_FRAME_HEIGHT, args.size[1])

src.set(cv2.CAP_PROP_FPS, 60)


while True:
    st = time.time()
    _, img = src.read()
    et = time.time()
    elapsed = 1.0 / (et - st) if (et - st) != 0 else -1.0
    #print(img.shape)
    print ("fps: %.1f" % elapsed)

    if not args.no_show:
        cv2.imshow("window", img)

        k = cv2.waitKey(1)

        if k != -1:
            break

