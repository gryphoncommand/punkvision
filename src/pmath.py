"""

Copyright 2017 LN STEMpunks

  This file is part of the punkvision project

  punkvision, punkvision Documentation, and any other resources in this 
project are free software; you are free to redistribute it and/or modify 
them under  the terms of the GNU General Public License; either version 
3 of the license, or any later version.

  These programs are hopefully useful and reliable, but it is understood 
that these are provided WITHOUT ANY WARRANTY, or MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GPLv3 or email at 
<info@chemicaldevelopment.us> for more info on this.

  Here is a copy of the GPL v3, which this software is licensed under. You 
can also find a copy at http://www.gnu.org/licenses/.


"""



import numpy
import cv2

# calculate FPS from stime to etime, but handles divide by sero
def elapsed_fps(stime, etime):
    dff = etime - stime
    if dff == 0:
        return 0
    else:
        return 1.0 / dff

class Pt():
    def __init__(self, v):
        if isinstance(v, numpy.ndarray):
            mu = cv2.moments(v, False)
            if mu["m00"] == 0:
                self.v = (None, None)
            else:
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
            if v == 0:
                return Pt([0 for i in range(0, len(self.v))])
            else:
                return Pt([self.v[i] / v for i in range(0, len(self.v))])
        else:
            return Pt([self.v[i] * v[i] for i in range(0, min(len(self.v), len(v)))])


