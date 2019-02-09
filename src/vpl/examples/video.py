
import sys
import os

import math
import tempfile

import argparse

parser = argparse.ArgumentParser(description='video processor')

parser.add_argument("source", nargs='?', default=0, help='camera source (can be video file as well) default is \'0\'')
parser.add_argument("-np", "--no-prop", action='store_true', help='use this flag to not use CameraProperties')
parser.add_argument("-i-s", "--input-size", default=None, type=str,  help="input size (WxH) to scale/request input as")

parser.add_argument("-i-o", "--input-output", default=None, help='output the input (without effects on it) to this location')

parser.add_argument("-loop", action='store_true', help='loop playback (i.e. play video over and over again)')


parser.add_argument('-p','--plugins', nargs='*', help='Add plugins')
parser.add_argument('-f','--files', nargs='*', help='Add file executors')


parser.add_argument("-ns", "--no-show", action='store_true', help='use this flag to not show')

parser.add_argument("-mjpg", "--mjpg-port", default=None, type=int, help='port to stream MJPG server to')

parser.add_argument("-o", "--output", default=None, help='output file')

parser.add_argument("-o-audio", "--output-audio", default=None, help='pair the finished video with an audio file or audio stream of a video (requires FFMPEG)')

parser.add_argument("-o-fps", "--output-fps", default=None, type=float, help='frames per second for encoding')

parser.add_argument("--dev", action='store_true', help='developer (non-install) flag')


args = parser.parse_args()

final_output = args.output
output = args.output

if args.output_audio is not None and args.output is not None:
    output = tempfile.mkstemp(suffix="." + args.output.split(".")[-1])[1]

if args.dev:
    sys.path.append(os.getcwd())

import vpl

# this line makes it easier
from vpl.all import *

pipe = Pipeline("pipe")

# input
vsrc = VideoSource(source=args.source, is_async=False, repeat=args.loop)

cam_props = CameraProperties()

cam_props["FPS"] = 60.0

# set preferred width and height
if args.input_size is not None and not args.no_prop:
    split = args.input_size.split("x")
    cam_props["FRAME_WIDTH"] = int(split[0])
    cam_props["FRAME_HEIGHT"] = int(split[1])

vsrc["properties"] = cam_props

pipe.add_vpl(vsrc)

if args.input_size is not None:
    split = args.input_size.split("x")
    pipe.add_vpl(Resize(size=(int(split[0]), int(split[1]))))

if args.input_output is not None:
    # TODO: do this better in VideoSource
    pipe.add_vpl(VideoSaver(path=args.input_output, is_async=False))

# processing here

#pipe.add_vpl(Bleed(N=2))
#pipe.add_vpl(Grayscale())
#pipe.add_vpl(Noise(level=.2))
#pipe.add_vpl(Bilateral(s_color=26, s_space=30))
#pipe.add_vpl(EdgeDiff())
#pipe.add_vpl(RainbowCrazy())
#pipe.add_vpl(HSLBin())

#pipe.add_vpl(Roll(w=lambda w, ct: 3.5 * ct, h=lambda h, ct: 5.5 * ct + h / 3.0 + 10 * math.sin(2 * math.pi * (h / 120.0 + ct / 24.0))))
#pipe.add_vpl(Grid(w=6, h=6))
#pipe.add_vpl(Pixelate())

#pipe.add_vpl(CoolChannelOffset(xoff=lambda i: 6 * i, yoff=lambda i: 1 * i))
#pipe.add_vpl(Scanlines())

#def transform_func(x, y, w, h):
#    return w * np.log(x + 1) / np.log(w), y

#pipe.add_vpl(Transform(func=transform_func))

if args.plugins is not None:
    for p in args.plugins:
        # evaluate plugin additions
        pipe.add_vpl(eval(p))
# just output

if args.files is not None:

    for f in args.files:
        # evaluate plugin additions
        exec(open(f, "r").read())

if args.dev:
    pipe.add_vpl(PrintInfo(fps=2, extended=True))

if args.mjpg_port is not None:
    pipe.add_vpl(MJPGServer(port=args.mjpg_port))

if not args.no_show:
    pipe.add_vpl(Display(title="window"))

if output is not None:
    vs = VideoSaver(path=output, is_async=False)
    if args.output_fps is not None:
        vs["fps"] = args.output_fps
    pipe.add_vpl(vs)


try:
    # we let our VideoSource do the processing, autolooping
    pipe.process(image=None, data=None, loop=True)
except (KeyboardInterrupt, SystemExit):
    print("keyboard interrupt, quitting")

print ("gracefully ending")

pipe.end()

if args.output_audio is not None and args.output is not None:
    pair_video_audio(final_output, output, args.output_audio)

