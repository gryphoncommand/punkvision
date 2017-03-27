
import numpy
import cv2

class Pt():
	def __init__(self, v):
		if isinstance(v, numpy.ndarray):
			mu = cv2.moments(v, False) 
			self.v = (mu["m10"]/mu["m00"], mu["m01"]/mu["m00"])
		else:
			self.v = v
		self.X = self.v[0]
		self.Y = self.v[1]
	
	def std(self):
		return tuple([int(vv) for vv in self.v])

	def __add__(self, v):
		if isinstance(v, Pt):
			return Pt([self.v[i] + v.v[i] for i in range(0, min(len(self.v), len(v.v)))])
		elif isinstance(v, int) or isinstance(v, float):
			rv = self.v
			rv[0] += v
			return Pt(rv)
		else:
			return Pt([self.v[i] + v[i] for i in range(0, min(len(self.v), len(v)))])

	def __sub__(self, v):
		if isinstance(v, Pt):
			return Pt([self.v[i] - v.v[i] for i in range(0, min(len(self.v), len(v.v)))])
		elif isinstance(v, int) or isinstance(v, float):
			rv = self.v
			rv[0] -= v
			return Pt(rv)
		else:
			return Pt([self.v[i] - v[i] for i in range(0, min(len(self.v), len(v)))])

	def __mul__(self, v):
		if isinstance(v, Pt):
			return Pt([self.v[i] * v.v[i] for i in range(0, min(len(self.v), len(v.v)))])
		elif isinstance(v, int) or isinstance(v, float):
			return Pt([self.v[i] * v for i in range(0, len(self.v))])
		else:
			return Pt([self.v[i] * v[i] for i in range(0, min(len(self.v), len(v)))])

	def __div__(self, v):
		if isinstance(v, Pt):
			return Pt([self.v[i] / v.v[i] for i in range(0, min(len(self.v), len(v.v)))])
		elif isinstance(v, int) or isinstance(v, float):
			return Pt([self.v[i] / v for i in range(0, len(self.v))])
		else:
			return Pt([self.v[i] * v[i] for i in range(0, min(len(self.v), len(v)))])


