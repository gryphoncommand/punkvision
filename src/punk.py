import sys
import os
import time
import math
import threading

import cv2
import numpy

import pmath

import argparse

# out of order color channels
def rgb(r, g, b):
	rs = r / 255.0
	gs = g / 255.0
	bs = b / 255.0
	minrgb = min([rs, gs, bs])
	maxrgb = max([rs, gs, bs])
	C = maxrgb - minrgb
	if maxrgb == rs:
		H = (bs - gs) / C
	elif maxrgb == bs:
		H = 2 + (gs - rs) / C
	elif maxrgb == gs:
		H = 4 + (rs - bs) / C
	L = (minrgb + maxrgb) / 2.0
	if L == 1.0 or L == 1:
		S = 0
	else:
		S = C / (1 - abs(2 * L - 1))
	H = H * 60
	S = S * 255
	L = L * 255
	return hsl(H, S, L)

# opencv expects HLS not HSL
def hsl(h, s, l):
	return (h, l, s)

default_filters = {
	"area": lambda x: x > 10,
}

default_vals = {
	"reg": False,

	"contour": rgb(120,60,20),
	"contour-thickness": 2,
	
	"reticle": rgb(120, 0, 0),
	"reticle-size": 12,
	"reticle-thickness": 2,
}

parser = argparse.ArgumentParser(description='PunkVision', formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50))

parser.add_argument('--source', '--input', default=None, help='source/input (/dev/videoX or dir/{0}.png)')
parser.add_argument('--save', '--output', type=str, default=None, help='saves the process input (dir/{0}.png)')
parser.add_argument('--save-every', '--output-every', type=int, default=2, help='save every X frames (useful for small disk sizes)')


parser.add_argument('--show', action='store_true', help='show image in a window')
parser.add_argument('--stream', type=int, default=None, help='stream to 0.0.0.0:X')

parser.add_argument('--file', '--config', default="configs/nothing.conf", help='config file')

parser.add_argument('--num', type=int, default=2, help='how many targets to find for a fit')
parser.add_argument('--size', type=int, nargs=2, default=(320, 240), help='image size')

parser.add_argument('-H', type=int, nargs=2, default=(0, 180), help='hue range')
parser.add_argument('-S', type=int, nargs=2, default=(0, 255), help='saturation range')
parser.add_argument('-L', type=int, nargs=2, default=(0, 255), help='luminance range')

parser.add_argument('-blur', type=int, nargs=2, default=(0, 0), help='blur size')
parser.add_argument('-exposure', type=float, default=0, help='exposure value')
parser.add_argument('-fps', type=float, default=10, help='frames per second from input')

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
		fit_dict[vals[0]] = eval("lambda x: {0}".format(vals[1]))
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

import imagepipe

pipe = imagepipe.ImagePipe(args)

stime, etime = 0, 0

while True:
	stime = time.time()
	pipe.update()
	pipe.process()
	if args.show:
		cv2.imshow("img", pipe.image())

	k = cv2.waitKey(1)
	etime = time.time()
	rtime = (1.0 / args.fps) - (etime - stime)
	if rtime > 0:
		time.sleep(rtime)

