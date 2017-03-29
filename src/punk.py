import sys
import os
import time
import argparse

import cv2
import numpy
from networktables import NetworkTables

import imagepipe
import pmath

# out of order color channels
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

default_filters = {
	"area": lambda area: area > 10,
}

default_vals = {
	"reg": False,
	"draw": True,

	"contour": rgb(120,60,20),
	"contour-thickness": 2,
	
	"reticle": rgb(120, 0, 0),
	"reticle-size": 12,
	"reticle-thickness": 2,
}

parser = argparse.ArgumentParser(description='PunkVision', formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50))

parser.add_argument('--source', '--input', default=None, help='source/input (/dev/videoX or dir/{0}.png)')
parser.add_argument('--save', '--output', type=str, default=None, help='saves the process input (dir/{0}.png)')
parser.add_argument('--save-every', '--output-every', type=int, default=1, help='save every X frames (useful for small disk sizes)')


parser.add_argument('--show', action='store_true', help='show image in a window')
parser.add_argument('--stream', type=int, default=None, help='stream to 0.0.0.0:X (9602)')

parser.add_argument('--publish', type=int, default=None, help='connect to NetworkTables at X (roboRIO-NNNN-frc.local)')
parser.add_argument('--table', type=str, default=None, help='NetworkTables table name (vision/gearpeg)')

parser.add_argument('--file', '--config', default="configs/nothing.conf", help='config file')

parser.add_argument('--num', type=int, default=2, help='how many targets to find for a fit')
parser.add_argument('--size', type=int, nargs=2, default=(320, 240), help='image size')

parser.add_argument('-H', type=int, nargs=2, default=(0, 180), help='hue range')
parser.add_argument('-S', type=int, nargs=2, default=(0, 255), help='saturation range')
parser.add_argument('-L', type=int, nargs=2, default=(0, 255), help='luminance range')

parser.add_argument('--buffer', type=int, default=None, help='blur size')
parser.add_argument('--blur', type=int, nargs=2, default=(0, 0), help='blur size')
parser.add_argument('-e', '--exposure', type=float, default=0, help='exposure value')
parser.add_argument('--fps', type=float, default=None, help='frames per second from input')

parser.add_argument('--fit', type=str, nargs='+', default=(), help='fitness switches ( dx:400 )')
parser.add_argument('--filter', type=str, nargs='*', default=(), help='filter values ( area:x>40 )')

parser.add_argument('-D', '--D', type=str, nargs='*', default=(), help='config values ( reticle:rgb(255,0,0) )')

args = parser.parse_args()

execfile(args.file)

# make tuples from lists
for v in vars(args):
	if isinstance(getattr(args, v), list):
		setattr(args, v, tuple(getattr(args, v)))

if not isinstance(args.fit, dict):
	fit_dict = {}
	for v in args.fit:
		vals = v.split(":")
		fit_dict[vals[0]] = float(vals[1])
	args.fit = fit_dict


if not isinstance(args.filter, dict):
	fit_dict = {}
	for v in args.filter:
		vals = v.split(":")
		fit_dict[vals[0]] = eval("lambda {0}: {1}".format(*vals))
	args.filter = fit_dict


for k in default_filters:
	if k not in args.filter:
		args.filter[k] = default_filters[k]


if not isinstance(args.D, dict):
	fit_dict = {}
	for v in args.D:
		vals = v.split(":")
		fit_dict[vals[0]] = eval(vals[1])
	args.D = fit_dict

for k in default_vals:
	if k not in args.D:
		args.D[k] = default_vals[k]

if args.publish:
    NetworkTables.initialize(server=args.publish)

def imageHandle(pipe):
	if pipe.args.show:
		cv2.imshow("img", pipe.im["output"])
		k = cv2.waitKey(1)

	if pipe.args.publish:
		table = NetworkTables.getTable(args.table)
		table.putNumber("fitness", pipe.fitness)
		table.putNumber("contours", len(pipe.contours))

		table.putNumber("x", pipe.center.X)
		table.putNumber("y", pipe.center.Y)

		table.putNumber("target_fps", pipe.args.fps)

		for key, fps in pipe.fps:
			table.putNumber("{0}_fps".format(key), fps)

		table.putNumber("width", pipe.args.size[0])
		table.putNumber("height", pipe.args.size[1])

		# it is only as fast as the slowest component
		table.putNumber("fps", min(pipe.fps.vals()))
		
		# just put so we know if it is updating
		table.putNumber("time", time.time())

pipe = imagepipe.ImagePipe(args, imageHandle=imageHandle)

pipe.start()

