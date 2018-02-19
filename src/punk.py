"""

Copyright 2017 LN STEMpunks

  This file is part of the punkvision project

  punkvision, punkvision Documentation, and any other resources in this 
project are free software; you are free to redistribute it and/or modify 
them under  the terms of the GNU General Public License; either version 
3 of the license, or any later version.

  These programs are hopefully useful and reliable, but it is understood 
that these are provided WITHOUT ANY WARRANTY, or MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GPLv3 or email at 
<info@chemicaldevelopment.us> for more info on this.

  Here is a copy of the GPL v3, which this software is licensed under. You 
can also find a copy at http://www.gnu.org/licenses/.


"""


import sys
import os
import time
import argparse


import vpl
import frcvpl

parser = argparse.ArgumentParser(description='PunkVision')

parser.add_argument('--source', '--input', default=0, help='source/input (/dev/videoX or "dir/*.png" or a video file)')

parser.add_argument('--save-input', type=str, default=None, help='saves the raw input ("dir/{num}.png" or video file)')

parser.add_argument('--save-output', type=str, default=None, help='saves the processed output ("dir/{num}.png" or video file)')

parser.add_argument('--save-every', type=int, default=1, help='save every X frames (useful for small disk sizes)')


parser.add_argument('--show', action='store_true', help='show image in a window')
parser.add_argument('--printinfo', action='store_true', help='prints info')
parser.add_argument('--stream', type=int, default=None, help='stream to 0.0.0.0:X (5802)')

parser.add_argument('--publish', type=str, default=None, help='connect to NetworkTables at X (roboRIO-NNNN-frc.local)')

parser.add_argument('--table', type=str, default=None, help='NetworkTables table name (vision/gearpeg)')

parser.add_argument('--size', type=int, nargs=2, default=(320, 240), help='image size')
parser.add_argument('--blur', type=int, nargs=2, default=(4, 4), help='image size')


#parser.add_argument('--file', '--config', default="configs/nothing.conf", help='config file')

#parser.add_argument('--num', type=int, default=1, help='how many groups to keep')
#parser.add_argument('--groupsize', type=int, default=2, help='how many targets to find for a fit in one group')

#parser.add_argument('-H', type=int, nargs=2, default=(0, 180), help='hue range')
#parser.add_argument('-S', type=int, nargs=2, default=(0, 255), help='saturation range')
#parser.add_argument('-L', type=int, nargs=2, default=(0, 255), help='luminance range')

#parser.add_argument('--buffer', type=int, default=None, help='blur size')

# replaced by -D blur:X,Y
#parser.add_argument('--blur', type=int, nargs=2, default=(0, 0), help='blur size')

#parser.add_argument('-e', '--exposure', type=float, default=None, help='exposure value')
#parser.add_argument('--fps', type=float, default=None, help='frames per second from input')

#parser.add_argument('--fit', type=str, nargs='+', default=(), help='fitness switches ( "myname:sum(abs(X-avg(X)))" )')
#parser.add_argument('--filter', type=str, nargs='*', default=(), help='filter values ( "myname: x > 40" )')

#parser.add_argument('-D', '--Dconfig', type=str, nargs='*', default=(), help='config values ( reticle:rgb(255,0,0) )')

args = parser.parse_args()

#execfile(args.file)
#exec(open(args.file, "r").read())

from vpl.all import *

pipe = Pipeline("punkvision")


# input
vsrc = VideoSource(source=args.source, async=False)

pipe.add_vpl(vsrc)

if args.printinfo:
    pipe.add_vpl(PrintInfo(fps=4, extended=True))

cam_props = CameraProperties()

cam_props["FPS"] = 60.0

#if args.exposure is not None:
#    cam_props["EXPOSURE"] = args.exposure

#if args.auto_exposure is not None and not args.no_prop:
#    cam_props["AUTO_EXPOSURE"] = args.auto_exposure

# set preferred width and height
cam_props["FRAME_WIDTH"] = args.size[0]
cam_props["FRAME_HEIGHT"] = args.size[1]

vsrc["properties"] = cam_props

# resize just in case
pipe.add_vpl(Resize(w=args.size[0], h=args.size[1]))

if args.save_input:
    pipe.add_vpl(VideoSaver(path=args.save_input, every=args.every))

# processing here


#blur
if args.blur is not None:
    pipe.add_vpl(Blur(w=args.blur[0], h=args.blur[1], method='box'))

#convert to HSV
pipe.add_vpl(ConvertColor(conversion=cv2.COLOR_BGR2HSV))

#Filter HSV threshold
pipe.add_vpl(frcvpl.InRange(mask_key="mask"))
pipe.add_vpl(frcvpl.ApplyMask(mask_key="mask"))

#Erode
pipe.add_vpl(frcvpl.StoreImage(key="normal"))
pipe.add_vpl(frcvpl.RestoreImage(key="mask"))
pipe.add_vpl(Erode())

#Dilate
pipe.add_vpl(Dilate())

#Find Contours
pipe.add_vpl(frcvpl.FindContours(key="contours"))

pipe.add_vpl(frcvpl.RestoreImage(key="normal"))

#Convert back to BGR
#pipe.add_vpl(frcvpl.ConvertColor(conversion=cv2.COLOR_HSV2BGR))

#Draws dot on center point of convex hull
pipe.add_vpl(frcvpl.DrawContours(key="contours"))

#Draws meter to tell how close to center
pipe.add_vpl(frcvpl.DrawMeter(key="contours"))

# add a FPS counter
pipe.add_vpl(FPSCounter())

pipe.add_vpl(frcvpl.DumpInfo(key="contours"))



# just output

pipe.add_vpl(FPSCounter())


if args.save_output:
    pipe.add_vpl(VideoSaver(path=args.save_output, every=args.every))

if args.stream is not None:
    pipe.add_vpl(MJPGServer(port=args.stream))

if args.show:
    pipe.add_vpl(Display(title="punkvision pipe"))

try:
    # we let our VideoSource do the processing, autolooping
    pipe.process(image=None, data=None, loop=True)
except (KeyboardInterrupt, SystemExit):
    print("keyboard interrupt, quitting")

print ("gracefully ending")

pipe.end()

