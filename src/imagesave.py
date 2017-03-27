
import cv2

class ImageSave():

	def __init__(self, imgdraw, args):
		self.imgdraw = imgdraw
		self.args = args

		self.im = None

		self.__num = 0
		self.__total_num = 0

	def saveImage(self):
		if self.__total_num % self.args.save_every == 0:
			cv2.imwrite(self.args.save.format(self.__num), self.imgdraw.getImage())
			self.__num += 1
		self.__total_num += 1
