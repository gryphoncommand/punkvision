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

import cv2
import numpy

#import imagepipe
import imageholder
import imagestream
import pmath

# out of order color channels
# see algorithm here: https://en.wikipedia.org/wiki/HSL_and_HSV
def rgb(r, g, b):
    rs = r / 255.0
    gs = g / 255.0
    bs = b / 255.0
    minrgb = min([rs, gs, bs])
    maxrgb = max([rs, gs, bs])
    L = (minrgb + maxrgb) / 2.0
    if L < 0.5:
        S = (maxrgb - minrgb) / (maxrgb + minrgb)
    else:
        S = (maxrgb - minrgb) / (2 - (maxrgb + minrgb))
    C = (maxrgb - minrgb)
    if maxrgb == rs:
        H = 60 * (gs - bs) / C
    elif maxrgb == gs:
        H = 120 + 60 * (bs - rs) / C
    elif maxrgb == bs:
        H = 240 + 60 * (rs - gs) / C
    if H < 0:
        H = H + 360
    H = H / 2.0
    S = S * 255
    L = L * 255
    return hsl(H, S, L)

# opencv expects HLS not HSL
def hsl(h, s, l):
    return (h, l, s)


def stddev(A):
    return numpy.std(A, ddof=1)

def avg(A):
    return numpy.average(A)


class Fit:
    def __init__(self, name, src):
        self.name = name
        self.src = src
        # capital because they are arrays
        self.__func = eval("lambda imgsize, X, Y, AREA: {0}".format(src))
    
    def func(self, imgsize, x, y, area):
        return self.__func(imgsize, x, y, area)

class Filter:
    def __init__(self, name, src):
        self.name = name
        self.src = src
        self.__func = eval("lambda imgsize, x, y, area: {0}".format(src))
    
    def func(self, imgsize, x, y, area):
        return self.__func(imgsize, x, y, area)


default_filters = {
    "_valid_x": Filter("_valid_x", "x is not None and x > 0")
#    "area": Filter("area", "area > 5")
}

default_fits = {
#    "_low_dx": Fit("_low_dx", "abs(X[1] - X[0]) * 10")
}


default_vals = {
    "normalize": False,
    "draw": True,

    # can be be (x, y)
    "blur": None,
    

    "contour": rgb(120,60,20),
    "contour-thickness": 2,
    
    "reticle": rgb(120, 0, 0),
    "reticle-size": 12,
    "reticle-thickness": 2,

    "contour-reticle": rgb(120, 0, 120),
    "contour-reticle-size": 8,
    "contour-reticle-thickness": 1,

}

parser = argparse.ArgumentParser(description='PunkVision', formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50))

parser.add_argument('--source', '--input', default="/dev/video0", help='source/input (/dev/videoX or "dir/*.png")')
parser.add_argument('--save-input', type=str, default=None, help='saves the raw input (dir/{num}.png)')
parser.add_argument('--save-output', type=str, default=None, help='saves the processed output (dir/{num}.png)')

parser.add_argument('--save-every', type=int, default=2, help='save every X frames (useful for small disk sizes)')


parser.add_argument('--show', action='store_true', help='show image in a window')
parser.add_argument('--stream', type=int, default=None, help='stream to 0.0.0.0:X (5802)')

parser.add_argument('--publish', type=str, default=None, help='connect to NetworkTables at X (roboRIO-NNNN-frc.local)')
parser.add_argument('--table', type=str, default=None, help='NetworkTables table name (vision/gearpeg)')

parser.add_argument('--file', '--config', default="configs/nothing.conf", help='config file')

parser.add_argument('--num', type=int, default=2, help='how many targets to find for a fit')
parser.add_argument('--size', type=int, nargs=2, default=(320, 240), help='image size')

parser.add_argument('-H', type=int, nargs=2, default=(0, 180), help='hue range')
parser.add_argument('-S', type=int, nargs=2, default=(0, 255), help='saturation range')
parser.add_argument('-L', type=int, nargs=2, default=(0, 255), help='luminance range')

parser.add_argument('--buffer', type=int, default=None, help='blur size')

# replaced by -D blur:X,Y
#parser.add_argument('--blur', type=int, nargs=2, default=(0, 0), help='blur size')

parser.add_argument('-e', '--exposure', type=float, default=None, help='exposure value')
parser.add_argument('--fps', type=float, default=None, help='frames per second from input')

parser.add_argument('--fit', type=str, nargs='+', default=(), help='fitness switches ( "myname:sum(abs(X-avg(X)))" )')
parser.add_argument('--filter', type=str, nargs='*', default=(), help='filter values ( "myname: x > 40" )')

parser.add_argument('-D', '--Dconfig', type=str, nargs='*', default=(), help='config values ( reticle:rgb(255,0,0) )')

args = parser.parse_args()

#execfile(args.file)
exec(open(args.file, "r").read())


# make tuples from lists
for v in vars(args):
    if isinstance(getattr(args, v), list):
        setattr(args, v, tuple(getattr(args, v)))

if not isinstance(args.fit, dict):
    fit_dict = {}
    for v in args.fit:
        vals = v.split(":")
        fit_dict[vals[0]] = Fit(vals[0], vals[1])
    args.fit = fit_dict


if not isinstance(args.filter, dict):
    fit_dict = {}
    for v in args.filter:
        vals = v.split(":")
        fit_dict[vals[0]] = Filter(vals[0], vals[1])
    args.filter = fit_dict


for k in default_filters:
    if k not in args.filter:
        args.filter[k] = default_filters[k]


if not isinstance(args.Dconfig, dict):
    fit_dict = {}
    for v in args.Dconfig:
        vals = v.split(":")
        fit_dict[vals[0]] = eval(vals[1])
    args.Dconfig = fit_dict

for k in default_vals:
    if k not in args.Dconfig:
        args.Dconfig[k] = default_vals[k]

if args.publish:
    from networktables import NetworkTables
    NetworkTables.initialize(server=args.publish)

def image_handler(holder):
    if args.show:
        if holder.im["output"] is not None:
            cv2.imshow("img", holder.im["output"])
            k = cv2.waitKey(1)

    if args.publish:
        table = NetworkTables.getTable(args.table)
        if holder.best_fitness:
            table.putNumber("fitness", holder.best_fitness)
        if holder.best_group:
            table.putNumber("contours", len(holder.best_group))

        table.putNumber("x", holder.best_center.X)
        table.putNumber("y", holder.best_center.Y)

        if args.fps:
            table.putNumber("target_fps", args.fps)
        else:
            table.putNumber("target_fps", -1)

        for key in holder.fps.keys():
            table.putNumber("{0}_fps".format(key), holder.fps[key])

        table.putNumber("width", args.size[0])
        table.putNumber("height", args.size[1])

        # it is only as fast as the slowest component
        min_fps = 0.0
        for x in holder.fps.values():
            if x != None:
                min_fps = min([min_fps, x])

        table.putNumber("fps", min_fps)
        
        # just put so we know if it is updating
        table.putNumber("last_time", time.time())

holder = imageholder.ImageHolder(args.source, args.size, args.H, args.L, args.S, args.num, args.exposure, args.fps, args.save_input, args.save_output, args.filter, args.fit, args.Dconfig, image_handler, save_every=args.save_every)

imagestream.holder = holder

holder.start()

if args.stream:
    imstream = imagestream.ThreadedHTTPServer(('0.0.0.0', args.stream), imagestream.StreamHandle)
    imstream.serve_forever()


#pipe = imagepipe.ImagePipe(args, imageHandle=imageHandle)

#pipe.start()

