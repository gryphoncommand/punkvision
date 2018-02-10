#!/usr/bin/env python3

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

"""

This is a simple cam viewer showing how vpl works

"""

import vpl
import cv2
import argparse

parser = argparse.ArgumentParser(description='Example webcam view for punkvision')

parser.add_argument('--source', type=str, default="0", help='camera number, image glob (like "data/*.png"), or video file ("x.mp4")')

parser.add_argument('--size', type=int, nargs=2, default=(640, 480), help='image size')
parser.add_argument('--blur', type=int, nargs=2, default=None, help='blur size')

parser.add_argument('--save', default=None, help='save the stream to files (ex: "data/{num}.png"')

parser.add_argument('--save-output', default=None, help='save the end stream to files (ex: "data/{num}.png"')

parser.add_argument('--stream', default=None, type=int, help='stream to a certain port (ex: "5802" and then connect to "localhost:5802" to view the stream)')

parser.add_argument('--noshow', action='store_true', help="if this flag is set, do not show a window (useful for raspberry PIs without a screen, you can use --stream)")

parser.add_argument('--noprop', action='store_true', help="if this flag is set, do not set capture properties (some may fail without this, use this if you are getting a QBUF error)")


args = parser.parse_args()


pipe = vpl.Pipeline("webcam")

cam_props = vpl.CameraProperties()

# set preferred width and height
if not args.noprop:
    cam_props["FRAME_WIDTH"] = args.size[0]
    cam_props["FRAME_HEIGHT"] = args.size[1]

# find the source
pipe.add_vpl(vpl.VideoSource(source=args.source, properties=cam_props))

# ensure the size
pipe.add_vpl(vpl.Resize(w=args.size[0], h=args.size[1]))

# optionally, save the results
if args.save is not None:
    pipe.add_vpl(vpl.VideoSaver(path=args.save))

# if we want to blur it
if args.blur is not None:
    pipe.add_vpl(vpl.Blur(w=args.blur[0], h=args.blur[1], method=vpl.BlurType.BOX))


#pipe.add_vpl(vpl.ConvertColor(conversion=cv2.COLOR_BGR2HLS))

#pipe.add_vpl(vpl.Pixelate())
#pipe.add_vpl(vpl.CoolChannelOffset())
#pipe.add_vpl(vpl.Bleed())

#pipe.add_vpl(vpl.Noise())
#pipe.add_vpl(vpl.Cartoon())
#pipe.add_vpl(vpl.DetailEnhance())

#pipe.add_vpl(vpl.ChannelSplit(store="my_channels"))
#pipe.add_vpl(vpl.ChannelRecombo(store="my_channels"))

# optionally, save the results
if args.save_output is not None:
    pipe.add_vpl(vpl.VideoSaver(path=args.save_output))

# add a FPS counter
pipe.add_vpl(vpl.FPSCounter())

# display it
if not args.noshow:
    pipe.add_vpl(vpl.Display(title="footage from " + str(args.source)))

if args.stream is not None:
    pipe.add_vpl(vpl.MJPGServer(port=args.stream))

try:
      # we let our VideoSource do the processing, autolooping
      pipe.process(image=None, data=None, loop=True)
except (KeyboardInterrupt, SystemExit):
    print("keyboard interrupt, quitting")
    exit(0)
    

