
import time

import threading
import multiprocessing

import cv2
import numpy as np

import inspect



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
  "AUTO_EXPOSURE": cv2.CAP_PROP_AUTO_EXPOSURE,
  "CONVERT_RGB": cv2.CAP_PROP_CONVERT_RGB,
  "RECTIFICATION": cv2.CAP_PROP_RECTIFICATION,

# not supported
#  "WHITE_BALANCE": cv2.CAP_PROP_WHITE_BALANCE,

}

# a list of valid image formats
valid_image_formats = [
    "png",
    "jpg", "jpeg", "jp2", ".jpe",
    "bmp",
    "dib",
    "webp",
    "pbm", "pgm", "ppm",
    "sr", "ras",
    "tiff", "tif"
]

# valid video formats (not official, just observed)
valid_video_formats = [
    "mov",
    "avi",
    "mp4",
    "mpeg",
    "flv",
    "mts"
]

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

        self.chain_time = (0, [])
        self.chain_fps = (0, [])
        self.chain_images = (None, [])

        self.vals = {}

        self.is_quit = False


    def __str__(self):
        ret = "Pipeline("

        if self.name != None:
            ret += "name='%s', " % self.name

        ret += "[ \n"


        for vpl in self.chain:
            ret += "  " + str(vpl) + ", \n"
        ret += "])"
        return ret

    def quit(self):
        """

        sets quit flag

        """
        self.is_quit = True


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

    def __raw_chain(self, im, data):
        chain_time = []

        chain_images = []

        for vpl in self.chain:
            st = time.time()
            im, data = vpl.process(self, im, data)
            et = time.time()
            if self.is_quit or im is None:
                break
            chain_images += [im.copy()]
            chain_time += [et - st]

        def fps(t):
            return 1.0 / t if t != 0 else float('inf')      
        
        if not self.is_quit:
            self.chain_images = im.copy(), chain_images
            self.chain_time = sum(chain_time), chain_time
            self.chain_fps = fps(sum(chain_time)), [fps(i) for i in chain_time]
            
        return im, data, chain_time

    def process(self, image, data=None, loop=False):
        """

        run through the chain, and process the image

        call it with image=None if you use a VideoSource() VPL plugin

        """

        if image is None:
            im = image
        else:
            im = image.copy()


        if data is None:
            data = dict()

        self.is_quit = False
        if loop:
            while not self.is_quit:
                im, data, chain_time = self.__raw_chain(im, data)
                if not self.is_quit:
                    pass
                    #print ("fps: " + "%.1f" % self.chain_fps[0])
        else:
            im, data, chain_time = self.__raw_chain(im, data)
            if not self.is_quit:
                pass
                #print ("fps: " + "%.1f" % self.chain_fps[0])
                
        return im, data

    def end(self):
        for vpl in self.chain:
            vpl.end()

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
        self.available_args = {}

        # builtin call
        self.register()

    def __str__(self):
        ret = "%s(" % (type(self).__name__)

        if self.name != None:
            ret += "name='%s'" % (self.name)

        ss = []
        for k in self.kwargs:
            v = self.kwargs[k]
            if isinstance(v, str):
                v = "'%s'" % v
            #elif isinstance(v, type(lambda _: None)):
            #    v = "(%s)" % inspect.getsourcelines(v)[0][0]
            
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

    def do_async(self, method, args=( )):
        thread = threading.Thread(target=method, args=args)
        thread.daemon = True
        thread.start()


    """

    implementable methods

    """

    def register(self):
        # use: self.available_args["w"] = "width of image"
        pass
        

    def process(self, pipe, image, data):
        """

        this is what actually happens to the image (the functionality of the plugin).

          * pipe : the Pipeline() class that called this method (which can be useful)
          * image : the image being processed
          * data : generic data that can be passed between plugins (as a dictionary)

        """

        return image, data

    def end(self):
        # called optionally as an end
        pass

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
        if self.get("is_async", False):
            self.do_async(self["pipe"].process, (image.copy(), data.copy()))
        else:
            self["pipe"].process(image.copy(), data.copy())
        return image, data

