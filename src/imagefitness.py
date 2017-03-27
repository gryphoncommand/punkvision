
import cv2
import pmath

class GenericFitness():

	def __init__(self, imgproc, args):
		self.imgproc = imgproc
		self.args = args

		self.im = None

	def __filter(self, contours):
		retcontours = []
		for i in range(0, len(contours)):
			good = True
			good = good and self.args.F["area"](cv2.contourArea(contours[i]))

			if good:
				retcontours.append(contours[i])
		return retcontours


	def __fitness(self, cont0, cont1):
		fit = 0
		try:
			center0 = pmath.Pt(cont0)
			center1 = pmath.Pt(cont1)
			
			area0 = cv2.contourArea(cont0)
			area1 = cv2.contourArea(cont1)
		except:
			return fit
		
		if "dx" in self.args.fit.keys():
			dx = abs(center1.X - center0.X)
			fit += self.args.fit["dx"] * dx
		if "dy" in self.args.fit.keys():
			dy = abs(center1.Y - center0.Y)
			fit += self.args.fit["dy"] * dy
		if "da" in self.args.fit.keys():
			da = abs(area1 - area0)
			fit += self.args.fit["da"] * da
		if "qa" in self.args.fit.keys():
			qa = float(area1) / area0
			if qa < 1:
				qa = 1.0 / qa
			fit += self.args.fit["qa"] * qa

		return fit

	def bestFit(self):
		cc = self.__filter(self.imgproc.getContours())
		max_indexes = (-1, -1)
		max_fitness = -float('inf')
		for x in range(0, len(cc)):
			for y in range(x+1, len(cc)):
				c_fit = self.__fitness(cc[x], cc[y])
				if c_fit > max_fitness:
					max_fitness = c_fit
					max_indexes = (x, y)
		if max_fitness == -float('inf') or -1 in max_indexes:
			return (None, (None, None))
		return (max_fitness, (cc[max_indexes[0]], cc[max_indexes[1]]))

	def getImage(self):
		return self.imgproc.getImage()
