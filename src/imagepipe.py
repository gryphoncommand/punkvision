
import os
import time
import threading

import cv2
import numpy

import pmath


class ImagePipe():
	def __init__(self, args):
		self.args = args

		self.inputType = ""

		self.im = None
		self.__get_num = 0
		self.__save_num = 0
		self.__total_save_num = 0

		if self.args.source.startswith("/dev/video"):
			l_int = len(self.args.source) - 1
			while l_int >= 0 and self.args.source[l_int].isdigit():
				l_int -= 1

			self.inputType = "cam"
			self.__camera_index = int(self.args.source[l_int+1:])
			self.__camera = cv2.VideoCapture(self.__camera_index)

			self.__camera.set(3, self.args.size[0])
			self.__camera.set(4, self.args.size[1])
			
			cmd = "v4l2-ctl -d /dev/video{0} -c exposure_auto=1 -c exposure_absolute={1}".format(self.__camera_index, self.args.exposure)
			os.system(cmd)
			time.sleep(.125)

		elif args.source is not None:
			self.inputType = "dir"
		
		self.__has_printed = {
			"resize": False,
			"num": False,
		}

		if self.args.save is not None:
			mkd = self.args.save.split("/")[0]
			if not os.path.exists(mkd):
				os.makedirs(mkd)

		if args.stream is not None:
			import imagestream
			imagestream.pipe = self
			self.stream = imagestream.ThreadedHTTPServer(('0.0.0.0', self.args.stream), imagestream.StreamHandle)
			pthread = threading.Thread(target=self.stream.serve_forever)
			pthread.start()

	def __print_once(self, title, msg):
		if title not in self.__has_printed or not self.__has_printed[title]:
			print (msg)
			self.__has_printed[title] = True

	def __update_im(self):
		if self.inputType == "cam":
			retval, self.im = self.__camera.read()
		elif self.inputType == "dir":
			self.im = cv2.imread(self.args.source.format(self.__get_num))
			self.__get_num += 1

	def __reg_im(self):
		height, width, depth = self.im.shape
		rr = numpy.sum(self.im[0:height,0:width:1]) / (height * width)
		self.im[::1] = numpy.multiply(self.im[::1], 100.0 / rr)

	def __mod_im(self):
		if 0 not in self.args.blur:
			self.im = cv2.blur(self.im, self.args.blur)


	def update(self):
		self.__update_im()
		while self.im is None or 0 in self.im.shape:
			self.__update_im()
		height, width, depth = self.im.shape
		if (width, height) != self.args.size:
			self.__print_once("resize", "Image had to be manually resized from {0} to {1}".format((width, height), self.args.size))
			self.im = cv2.resize(self.im, self.args.size, interpolation=cv2.INTER_CUBIC)
		self.im = cv2.cvtColor(self.im, cv2.COLOR_BGR2HLS)		
		if self.args.D["reg"] not in (False, None):
			self.__reg_im()
		self.__mod_im()


	def __fitness_contours(self, contours):
		fit = 0
		try:
			centers = [pmath.Pt(c) for c in contours]
			areas = [cv2.contourArea(c) for c in contours]
		except:
			return fit
		
		if "dx" in self.args.fit.keys():
			avgx = sum([center.X for center in centers]) / float(len(centers))
			avgdx = sum([abs(center.X - avgx) for center in centers]) / float(len(centers))
			fit += self.args.fit["dx"] * avgdx
		if "dy" in self.args.fit.keys():
			avgy = sum([center.Y for center in centers]) / float(len(centers))
			avgdy = sum([abs(center.Y - avgy) for center in centers]) / float(len(centers))
			fit += self.args.fit["dy"] * avgdy
		if "da" in self.args.fit.keys():
			avga = sum([areas[i] for i in range(0, len(areas))]) / float(len(areas))
			avgda = sum([abs(areas[i] - avga) for i in range(0, len(areas))]) / float(len(areas))
			fit += self.args.fit["da"] * avgda

		# geometric average of areas
		if "qa" in self.args.fit.keys():
			avgqa = 1
			for area in areas:
				avgqa *= area ** (1.0 / len(areas))
			def __qa(a0, avg):
				ret = float(a0) / avg
				if ret < 1: ret = 1.0 / ret
				return ret

			avgda = sum([abs(areas[i] - avga) for i in range(0, len(areas))]) / float(len(areas))

			qa = float(area1) / area0
			if qa < 1:
				qa = 1.0 / qa
			fit += self.args.fit["qa"] * qa

		return fit

	def __get_best_fit(self):
		cc = self.__get_filtered_contours()
		num = self.args.num
		if num > len(cc):
			num = len(cc)
			self.__print_once("num", "Not enough contours found, so assuming use the max amount of contours")
		max_indexes = tuple([-1] * num)
		max_fitness = -float('inf')
		import itertools
		for indexes in itertools.combinations(range(0, len(cc)), num):
			c_fit = self.__fitness_contours([cc[i] for i in indexes])
			if c_fit > max_fitness:
				max_fitness = c_fit
				max_indexes = tuple([i for i in indexes])
		if max_fitness == -float('inf') or -1 in max_indexes:
			return (None, (None, None))
		return (max_fitness, tuple([cc[i] for i in max_indexes]))


	def __get_filtered_contours(self):
		__cvt = cv2.inRange(self.im, (self.args.H[0], self.args.L[0], self.args.S[0]),  (self.args.H[1], self.args.L[1], self.args.S[1]))
		contours, hierarchy = cv2.findContours(__cvt, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)
		retcontours = []
		for i in range(0, len(contours)):
			good = True
			good = good and self.args.filter["area"](cv2.contourArea(contours[i]))

			if good:
				retcontours.append(contours[i])
		return retcontours

	def __draw_im(self):
		__im_draw = self.im.copy()
		fitness, contours = self.__get_best_fit()

		if fitness != None:
			centers = [pmath.Pt(c) for c in contours]
			areas = [cv2.contourArea(c) for c in contours]
			center = pmath.Pt((0, 0))
			for _cen in centers:
				center += _cen
			center = center / float(len(centers))

			if not self.args.D["contour"] in (False, None):
				for i in range(0, len(contours)):
					cv2.drawContours(__im_draw, contours, i, self.args.D["contour"], self.args.D["contour-thickness"])
			
			if not self.args.D["reticle"] in (False, None):
				retcol = self.args.D["reticle"]
				retsize = self.args.D["reticle-size"]
				retthickness = self.args.D["reticle-thickness"]
				cv2.circle(__im_draw, center.std(), self.args.D["reticle-size"], retcol, retthickness)
				offX = pmath.Pt((retsize, 0))
				offY = pmath.Pt((0, retsize))
				cv2.line(__im_draw, (center - offX).std(), (center + offX).std(), retcol, retthickness)
				cv2.line(__im_draw, (center - offY).std(), (center + offY).std(), retcol, retthickness)
		return __im_draw

	def __get_im(self):
		return self.im
	
	def __get_final_im(self):
		return cv2.cvtColor(self.__draw_im(), cv2.COLOR_HLS2BGR)
	
	def __save_im(self):
		if self.__total_save_num % self.args.save_every == 0:
			cv2.imwrite(self.args.save.format(self.__save_num), self.__get_final_im())
			self.__save_num += 1
		self.__total_save_num += 1

	def image(self):
		return self.__get_final_im()

	def process(self):
		if self.args.save is not None:
			self.__save_im()

