"""

Copyright 2017 LN STEMpunks & ChemicalDevelopment

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


from enum import Enum

import cv2

class BlurType(Enum):

    """

    Enums for different blur types

    """

    BOX = 1
    GAUSSIAN = 2
    MEDIAN = 3


"""

definition of all opencv cap props

"""

cap_prop_lookup = {
  "POS_MSEC": cv2.CAP_PROP_POS_MSEC,
  "POS_FRAMES": cv2.CAP_PROP_POS_FRAMES,
  "POS_AVI_RATIO": cv2.CAP_PROP_POS_AVI_RATIO,
  "FRAME_WIDTH": cv2.CAP_PROP_FRAME_WIDTH,
  "FRAME_HEIGHT": cv2.CAP_PROP_FRAME_HEIGHT,
  "FPS": cv2.CAP_PROP_FPS,
  "FOURCC": cv2.CAP_PROP_FOURCC,
  "FRAME_COUNT": cv2.CAP_PROP_FRAME_COUNT,
  "FORMAT": cv2.CAP_PROP_FORMAT,
  "MODE": cv2.CAP_PROP_MODE,
  "BRIGHTNESS": cv2.CAP_PROP_BRIGHTNESS,
  "CONTRAST": cv2.CAP_PROP_CONTRAST,
  "SATURATION": cv2.CAP_PROP_SATURATION,
  "HUE": cv2.CAP_PROP_HUE,
  "GAIN": cv2.CAP_PROP_GAIN,
  "EXPOSURE": cv2.CAP_PROP_EXPOSURE,
  "CONVERT_RGB": cv2.CAP_PROP_CONVERT_RGB,
  "RECTIFICATION": cv2.CAP_PROP_RECTIFICATION,
# not supported
#  "WHITE_BALANCE": cv2.CAP_PROP_WHITE_BALANCE,

}

class CameraProperties:

    def __init__(self, **kwargs):
        self.props = kwargs
        for x in kwargs:
            if x not in cap_prop_lookup.keys():
                raise KeyError("invalid CAP_PROP: %s" % x)

    def __str__(self):
        ret = "%s(" % (type(self).__name__)
        ss = []
        for p in self.props.keys():
            v = self.props[p]
            if isinstance(v, str):
                v = "'%s'" % v
            ss += ["%s=%s" % (p, v)]
        ret += ",".join(ss)
        ret += ")"
        return ret

    def __getitem__(self, key, default=None):
        return self.props.get(key, default)

    def __setitem__(self, key, val):
        self.props[key] = val


"""

vpl = video pipe line

Think of it similar to how VSTs handle audio, this is a plugin for video

"""


import cv2


class Pipeline:

    def __init__(self, name=None, chain=None):
        self.name = name

        # these are the VPL classes that process the image
        if chain is None:
            self.chain = []
        else:
            self.chain = chain

        self.vals = {}

    def __str__(self):
        ret = "Pipeline("

        if self.name != None:
            ret += "name='%s', " % self.name

        ret += "[ \n"


        for vpl in self.chain:
            ret += "  " + str(vpl) + ", \n"
        ret += "])"
        return ret

    def add_vpl(self, vpl):
        """

        adds a plugin to the pipeline (at the end), and returns the index in the chain

        """
        self.chain += [vpl]
        return len(self.chain) - 1

    def remove_vpl(self, vpl):
        """

        removes a plugin from the pipeline, or if it is an int, remove that index

        returns either what you passed it, or if it was an int, return the removed plugin

        """
        if isinstance(vpl, int):
            return self.chain.pop(vpl)
        else:
            self.chain.remove(vpl)
            return vpl


    def process(self, image):
        """

        run through the chain, and process the image

        call it with image=None if you use a VideoSource() VPL plugin

        """

        if image is None:
            im = image
        else:
            im = image.copy()

        for vpl in self.chain:
            im = vpl.process(im)
        
        return im

    def __getitem__(self, key, default=None):
        return self.vals.get(key, default)

    get = __getitem__


    def __setitem__(self, key, val):
        self.vals[key] = val


class VPL:
    
    def __init__(self, name=None, **kwargs):
        """

        initialized with a name, and arguments, which you can get later using self["key"], or set using self["key"] = val

        """

        self.name = name
        self.kwargs = kwargs

    def __str__(self):
        ret = "%s(" % (type(self).__name__)

        if self.name != None:
            ret += "name='%s'" % (self.name)

        ss = []
        for k in self.kwargs:
            v = self.kwargs[k]
            if isinstance(v, str):
                v = "'%s'" % v
            
            ss += ["%s=%s" % (k, v)]

        ret += ", ".join(ss)

        ret += ")"
        return ret

    """

    helper methods

    """

    def __getitem__(self, key, default=None):
        return self.kwargs.get(key, default)

    get = __getitem__

    def __setitem__(self, key, val):
        self.kwargs[key] = val


    def process(self, pipe, image):
        """

        this is what actually happens to the image (the functionality of the plugin).

        You should have `pipe` and `image`, which are references to the Pipeline that called it, and the image that is to be processed

        """

        return image

class VideoSource(VPL):
    """

    Usage: VideoSource(id=0)

    optional arguments:

      * "camera" = camera object (default of None)
      * "id" = camera index (default of 0)
      * "properties" = CameraProperties() object with CAP_PROP values (see that class for info)

    this sets the image to a camera.

    THIS CLEARS THE IMAGE THAT WAS BEING PROCESSED, USE THIS AS THE FIRST PLUGIN

    """

    def process(self, image):
        if self["camera"] is None:
            self["camera"] = cv2.VideoCapture(self.get("id", 0))
            
            props = self["properties"]
            if props != None:
                for p in props.props:
                    print ("setting: " + str(cap_prop_lookup[p]) + " to: " + str(type(props[p])))
                    self["camera"].set(cap_prop_lookup[p], props[p])

        return self["camera"].read()[1]

class Resize(VPL):
    """

    Usage: Resize(w=512, h=256)

      * "w" = width, in pixels
      * "h" = height, in pixels

    optional arguments:

      * "method" = opencv resize method, default is cv2.INTER_LINEAR

    """

    def process(self, image):
        height, width, depth = image.shape

        if width != self["w"] or height != self["h"]:
            resize_method = self.get("method", cv2.INTER_LINEAR)
            return cv2.resize(image, (self["w"], self["h"]), interpolation=resize_method)
        else:
            # if it is the correct size, don't spend time resizing it
            return image


class Blur(VPL):
    """

    Usage: Blur(w=4, h=8)

      * "w" = width, in pixels (for guassian blur, w % 2 == 1) (for median blur, this must be an odd integer greater than 1 (3, 5, 7... are good))
      * "h" = height, in pixels (for guassian blur, w % 2 == 1) (for median blur, this is ignored)

    optional arguments:

      * "method" = opencv blur method, default is vpl.BlurType.BOX
      * "sx" = 'sigma x' for the Gaussian blur standard deviation, defaults to letting OpenCV choose based on image size
      * "sy" = 'sigma y' for the Gaussian blur standard deviation, defaults to letting OpenCV choose based on image size

    """

    def process(self, image):
        if self["w"] in (0, None) or self["h"] in (0, None):
            return image
        else:
            resize_method = self.get("method", BlurType.BOX)

            if resize_method == BlurType.GAUSSIAN:
                sx, sy = self.get("sx", 0), self.get("sy", 0)
                return cv2.GaussianBlur(image, (self["w"], self["h"]), sigmaX=sx, sigmaY=sy)
            elif resize_method == BlurType.MEDIAN:
                return cv2.medianBlur(image, self["w"])
            else:
                # default is BlurType.BOX
                return cv2.blur(image, (self["w"], self["h"]))        

class Display(VPL):
    """

    Usage: Display(title="mytitle")

        * "title" = the window title

    """

    def process(self, image):

        cv2.imshow(self["title"], image)
        cv2.waitKey(1)

        return image


class PrintInfo(VPL):
    """

    Usage: PrintInfo()


    This prints out info about the image

    """

    def process(self, image):
        h, w, d = image.shape
        print ("width=%s, height=%s" % (w, h))
        return image



pipe = Pipeline("mypipe")

cam_props = CameraProperties()

cam_props["FRAME_WIDTH"] = 640
cam_props["FRAME_HEIGHT"] = 480

pipe.add_vpl(VideoSource(id=0, properties=cam_props))
pipe.add_vpl(PrintInfo())
#pipe.add_vpl(Resize(w=1280, h=720))
#pipe.add_vpl(Blur(w=63, h=63, method=BlurType.MEDIAN))
pipe.add_vpl(Display(title="mytitle"))

while True:
    # we let our VideoSource do the processing
    pipe.process(image=None)

