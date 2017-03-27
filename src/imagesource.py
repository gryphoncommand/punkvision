import time
import os
import cv2
import numpy

class DirectoryImageSource():

	def __init__(self, args):
		self.im = None
		self.args = args
		self.__num = 0

	def __get_image(self):
		self.im = cv2.imread(self.args.source.format(self.__num))
		self.__num += 1

	def reg(self):
		height, width, depth = self.im.shape
		rr = numpy.sum(self.im[0:height,0:width:1]) / (height * width)
		self.im[::1] = numpy.multiply(self.im[::1], 100.0 / rr)

	def update(self):
		self.__get_image()
		while self.im is None or 0 in self.im.shape:
			self.__get_image()
		self.im = cv2.cvtColor(self.im, cv2.COLOR_BGR2HLS)
		#self.reg()
		height, width, depth = self.im.shape
		if (width, height) != self.args.size:
			self.im = cv2.resize(self.im, self.args.size, interpolation = cv2.INTER_CUBIC)

	def get(self):
		return self.im

class CameraImageSource():

	def __init__(self, args):
		self.im = None

		self.args = args
		self.__camera = cv2.VideoCapture(args.source)

		self.__camera.set(3, args.size[0])
		self.__camera.set(4, args.size[1])
		
		cmd = "v4l2-ctl -d /dev/video{0} -c exposure_auto=1 -c exposure_absolute={1}".format(self.args.source, self.args.exposure)
		os.system(cmd)
		time.sleep(.125)

		self.__has_printed = False

	def __get_image(self):
		retval, self.im = self.__camera.read()

	def reg(self):
		height, width, depth = self.im.shape
		rr = numpy.sum(self.im[0:height,0:width:1]) / (height * width)
		self.im[::1] = numpy.multiply(self.im[::1], 100.0 / rr)

	def update(self):
		self.__get_image()
		while self.im is None or 0 in self.im.shape:
			self.__get_image()
		self.im = cv2.cvtColor(self.im, cv2.COLOR_BGR2HLS)
		#self.reg()
		height, width, depth = self.im.shape
		if (width, height) != self.args.size:
			self.im = cv2.resize(self.im, self.args.size, interpolation = cv2.INTER_CUBIC)

	def get(self):
		return self.im



"""
class ImageCameraSource():

	def __init__(self, args):
		self.im = None
		self.retval = None

		self.args = args

		self.__camera = cv2.VideoCapture(args.camera)

		self.__camera.set(3, args.size[0])
		self.__camera.set(4, args.size[1])

		self.__has_printed = False


	def reg(self):
		height, width, depth = self.im.shape
		rr = 100 * height * width / numpy.sum(self.im[0:height,0:width:1])
		self.im[::1] = numpy.multiply(self.im[::1], rr)

	def update(self):
		self.__last_im = self.im
		self.retval, self.im = self.__camera.read()
		self.im = cv2.cvtColor(self.im, cv2.COLOR_BGR2HLS)
		#self.reg()
		if self.im is None or 0 in self.im.shape:
			self.im = self.__last_im
			self.update()
			return
		height, width, depth = self.im.shape
		if (width, height) != self.args.size:
			if not self.__has_printed:
				print ("Image had to be manually resized from {0} to {1}".format((width, height), self.args.size))
				self.__has_printed = True
			self.im = cv2.resize(self.im, self.args.size, interpolation = cv2.INTER_CUBIC)


	def get(self):
		self.update()
		return self.im


"""