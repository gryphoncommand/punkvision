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
import time
import threading
import math
import os
import pathlib


import cv2

import numpy as np

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

        self.chain_time = []
        self.chain_fps = (0, [])

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


    def process(self, image, data=None):
        """

        run through the chain, and process the image

        call it with image=None if you use a VideoSource() VPL plugin

        """

        if image is None:
            im = image
        else:
            im = image.copy()

        chain_time = []

        if data is None:
            data = {}

        for vpl in self.chain:
            st = time.time()
            im, data = vpl.process(self, im, data)
            et = time.time()
            chain_time += [et - st]
        
        self.chain_time = sum(chain_time), chain_time
        self.chain_fps = 1.0 / sum(chain_time), [1.0 / i if i != 0 else float('inf') for i in chain_time]
        
        return im, data

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


    """

    for async operations, you can call this and it doesn't stall

    """

    def do_async(self, method, args=()):
        thread = threading.Thread(target=method, args=args)
        thread.start()

    def process(self, pipe, image, data):
        """

        this is what actually happens to the image (the functionality of the plugin).

          * pipe : the Pipeline() class that called this method (which can be useful)
          * image : the image being processed
          * data : generic data that can be passed between plugins (as a dictionary)

        """

        return image, data

class SubVPL(VPL):
    """

    This is a control VPL, it treats a Pipeline as a single VPL, so you can embed stuff in a VPL

    Usage: SubVPL(pipe=Pipeline(...))

      * "pipe" = pipeline to run as a VPL

    """

    def process(self, pipe, image, data):
        return self["pipe"].process(image, data)


class ForkVPL(VPL):
    """

    This is a control VPL, it forks and runs another Pipeline in another thread.

    This is useful for things that publish to network tables, or look for different vision targets

    Usage: ForkVPL(pipe=Pipeline(...))

      * "pipe" = pipeline to run as a VPL

    THIS ONLY RETURNS THE IMAGE PASSED TO IT

    """

    def process(self, pipe, image, data):
        self.do_async(self["pipe"].process, (image.copy(), data.copy()))
        return image, data


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

    def process(self, pipe, image, data):
        if self["camera"] is None:
            self["camera"] = cv2.VideoCapture(self.get("id", 0))
            
            props = self["properties"]
            if props != None:
                for p in props.props:
                    #print ("setting: " + str(cap_prop_lookup[p]) + " to: " + str(type(props[p])))
                    self["camera"].set(cap_prop_lookup[p], props[p])

        return self["camera"].read()[1], data

class VideoSaver(VPL):
    """

    Usage: VideoSaver(path="data/{num}.png")

      * "path" = image format


    optional arguments:
    
      * "every" = save every N frames (default 1 for every frame)

    Saves images as they are received to their destination

    """

    def save_image(self, image, num):
        loc = pathlib.Path(self["path"].format(num=num))
        if not loc.parent.exists():
            loc.parent.mkdir(parents=True)
        cv2.imwrite(str(loc), image)

    def process(self, pipe, image, data):
        if not hasattr(self, "num"):
            self.num = 0
        
        if self.num % self.get("every", 1) == 0:
            # async save it
            self.do_async(self.save_image, (image.copy(), self.num))

        self.num += 1

        return image, data


class Resize(VPL):
    """

    Usage: Resize(w=512, h=256)

      * "w" = width, in pixels
      * "h" = height, in pixels

    optional arguments:

      * "method" = opencv resize method, default is cv2.INTER_LINEAR

    """

    def process(self, pipe, image, data):
        height, width, depth = image.shape

        if width != self["w"] or height != self["h"]:
            resize_method = self.get("method", cv2.INTER_LINEAR)
            return cv2.resize(image, (self["w"], self["h"]), interpolation=resize_method)
        else:
            # if it is the correct size, don't spend time resizing it
            return image, data


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

    def process(self, pipe, image, data):
        if self["w"] in (0, None) or self["h"] in (0, None):
            return image, data
        else:
            resize_method = self.get("method", BlurType.BOX)

            if resize_method == BlurType.GAUSSIAN:
                sx, sy = self.get("sx", 0), self.get("sy", 0)
                return cv2.GaussianBlur(image, (self["w"], self["h"]), sigmaX=sx, sigmaY=sy), data
            elif resize_method == BlurType.MEDIAN:
                return cv2.medianBlur(image, self["w"]), data
            else:
                # default is BlurType.BOX
                return cv2.blur(image, (self["w"], self["h"])), data


class Display(VPL):
    """

    Usage: Display(title="mytitle")

        * "title" = the window title

    """

    def process(self, pipe, image, data):

        cv2.imshow(self["title"], image)
        cv2.waitKey(1)

        return image, data


class PrintInfo(VPL):
    """

    Usage: PrintInfo()


    This prints out info about the image and pipeline

    """

    def process(self, pipe, image, data):
        h, w, d = image.shape
        print ("width=%s, height=%s" % (w, h))
        return image, data


class FPSCounter(VPL):
    """

    Usage: FPSCounter()


    Simply adds the FPS in the bottom left corner

    """

    def process(self, pipe, image, data):
        font = cv2.FONT_HERSHEY_SIMPLEX
        height, width, _ = image.shape
        geom_mean = math.sqrt(height * width)
        offset = geom_mean * .01
        image = cv2.putText(image, "%2.1f" % pipe.chain_fps[0], (int(offset), int(height - offset)), font, offset / 6.0, (255, 0, 0), int(offset / 6.0 + 2))
        return image, data

