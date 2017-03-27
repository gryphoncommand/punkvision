import cv2

class ImageProcess():
	def __init__(self, imgsrc, args):
		self.imgsrc = imgsrc
		self.args = args
		self.im = None

	def getImage(self):
		self.im = self.imgsrc.get()
		if 0 not in self.args.blur:
			self.im = cv2.blur(self.im, self.args.blur)
		return self.im

	def getContours(self):
		self.getImage()
		self.__cvt = cv2.inRange(self.im, (self.args.H[0], self.args.L[0], self.args.S[0]),  (self.args.H[1], self.args.L[1], self.args.S[1]))
		#cv2.imshow("CVT img", self.__cvt)
		self.contours, self.hierarchy = cv2.findContours(self.__cvt, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)
		return self.contours
