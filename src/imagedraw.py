
import cv2
import pmath

class ImageDraw():

	def __init__(self, imgfit, args):
		self.imgfit = imgfit
		self.args = args

		self.im = None
		self.__im_draw = self.im


	def getImage(self):
		self.im = self.imgfit.getImage()
		self.__im_draw = self.im.copy()
		self.fitness, self.contours = self.imgfit.bestFit()

		if self.fitness != None:
			center0, center1 = pmath.Pt(self.contours[0]), pmath.Pt(self.contours[1])
			center = (center0 + center1) / 2
			cv2.drawContours(self.__im_draw, self.contours, 0, self.args.C["contour"], 2)
			cv2.drawContours(self.__im_draw, self.contours, 1, self.args.C["contour"], 2)
			
			if self.args.D["reticle"]:
				retcol = self.args.C["reticle"]
				retsize = self.args.D["reticle-size"]
				retthickness = self.args.D["reticle-thickness"]
				cv2.circle(self.__im_draw, center.std(), self.args.D["reticle-size"], retcol, retthickness)
				offX = pmath.Pt((retsize, 0))
				offY = pmath.Pt((0, retsize))
				cv2.line(self.__im_draw, (center - offX).std(), (center + offX).std(), retcol, retthickness)
				cv2.line(self.__im_draw, (center - offY).std(), (center + offY).std(), retcol, retthickness)

		return self.__im_draw

