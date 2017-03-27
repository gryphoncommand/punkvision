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
def rgb(r, b, g):
	rs = r / 255.0
	gs = g / 255.0
	bs = b / 255.0
	minrgb = min([rs, gs, bs])
	maxrgb = max([rs, gs, bs])
	C = maxrgb - minrgb
	if maxrgb == rs:
		H = (gs - bs) / C
	elif maxrgb == gs:
		H = 2 + (bs - rs) / C
	elif maxrgb == bs:
		H = 4 + (rs - gs) / C
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


default_colors = {
	"contour": rgb(255,140,0),
	"reticle": rgb(120, 0, 0),
}

default_filters = {
	"area": lambda x: x > 10,
}

default_vals = {
	"contour": True,
	"reticle": True,
	"reticle-size": 10,
	"reticle-thickness": 2,
}

parser = argparse.ArgumentParser(description='PunkVision', formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50))

parser.add_argument('--source', '--input', default=None, help='source/input (/dev/videoX or dir/{0}.png)')
parser.add_argument('--save', '--output', type=str, default=None, help='saves the process input (dir/{0}.png)')
parser.add_argument('--save-every', '--output-every', type=int, default=2, help='save every X frames (useful for small disk sizes)')


parser.add_argument('--show', action='store_true', help='show image in a window')
parser.add_argument('--stream', type=int, default=None, help='stream to 0.0.0.0:X')

parser.add_argument('--file', '--config', default="configs/nothing.conf", help='config file')
parser.add_argument('--fit', type=str, nargs='+', default=(), help='fitness switches (x:400, y:200)')

parser.add_argument('--size', type=int, nargs=2, default=(320, 240), help='image size')

parser.add_argument('-H', type=int, nargs=2, default=(0, 180), help='hue range')
parser.add_argument('-S', type=int, nargs=2, default=(0, 255), help='saturation range')
parser.add_argument('-L', type=int, nargs=2, default=(0, 255), help='luminance range')

parser.add_argument('-blur', type=int, nargs=2, default=(0, 0), help='blur size')
parser.add_argument('-exposure', type=float, default=0, help='exposure value')
parser.add_argument('-fps', type=float, default=10, help='frames per second from input')

parser.add_argument('-C', '--C', type=str, nargs='*', default=(), help='color values')
parser.add_argument('-D', '--D', type=str, nargs='*', default=(), help='random values')
parser.add_argument('-F', '--F', type=str, nargs='*', default=(), help='filter values (area:x>40)')

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


if not isinstance(args.F, dict):
	fit_dict = {}
	for v in args.F:
		vals = v.split(":")
		print vals[1]
		fit_dict[vals[0]] = eval("lambda x: {0}".format(vals[1]))
	args.F = fit_dict


for k in default_filters:
	if k not in args.F:
		args.F[k] = default_filters[k]

if not isinstance(args.C, dict):
	fit_dict = {}
	for v in args.C:
		vals = v.split(":")
		fit_dict[vals[0]] = eval(vals[1])
	args.C = fit_dict

for k in default_colors:
	if k not in args.C:
		args.C[k] = default_colors[k]


if not isinstance(args.D, dict):
	fit_dict = {}
	for v in args.D:
		vals = v.split(":")
		fit_dict[vals[0]] = eval(vals[1])
	args.D = fit_dict

for k in default_vals:
	if k not in args.D:
		args.D[k] = default_vals[k]

import imagesource
import imageproc
import imagefitness
import imagedraw
import imagestream
import imagesave

src = None
stream = None

if args.source.startswith("/dev/video"):
	l_int = len(args.source) - 1
	while l_int >= 0 and args.source[l_int].isdigit():
		l_int -= 1
	args.source = int(args.source[l_int+1:])
	src = imagesource.CameraImageSource(args)
elif args.source is not None:
	src = imagesource.DirectoryImageSource(args)

proc = imageproc.ImageProcess(src, args)
fit = imagefitness.GenericFitness(proc, args)
draw = imagedraw.ImageDraw(fit, args)

if args.stream is not None:
	stream = imagestream.ThreadedHTTPServer(('0.0.0.0', args.stream), imagestream.StreamHandle)
	imagestream.imgdraw = draw
	pthread = threading.Thread(target=stream.serve_forever)
	pthread.start()

save = None

if args.save is not None:
	mkd = args.save.split("/")[0]
	if not os.path.exists(mkd):
		os.makedirs(mkd)
	save = imagesave.ImageSave(draw, args)

stime, etime = 0, 0

while True:
	stime = time.time()
	src.update()
	im = draw.getImage()
	if args.show:
		cv2.imshow("img", cv2.cvtColor(im, cv2.COLOR_HLS2BGR))
	if args.save is not None:
		save.saveImage()
	k = cv2.waitKey(1)
	etime = time.time()
	rtime = (1.0 / args.fps) - (etime - stime)
	if rtime > 0:
		time.sleep(rtime)

