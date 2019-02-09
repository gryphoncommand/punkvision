"""

input/output

"""

from vpl import VPL

from vpl.defines import cap_prop_lookup

import cv2
import numpy as np

import glob

import vpl

import subprocess

import os
import time
import pathlib

class VideoSource(VPL):
    """

    Usage: VideoSource(source=0)
-rw-rw-r-- 1 cade cade 36M Feb 17 00:20 ../src/0.avi

    optional arguments:

      * "source" = camera index (default of 0), or a string containing a video file (like "VIDEO.mp4") or a string containing images ("data/*.png")
      * "properties" = CameraProperties() object with CAP_PROP values (see that class for info)
      * "repeat" = whether to repeat the image sequence (default False)
    
    this sets the image to a camera.

    THIS CLEARS THE IMAGE THAT WAS BEING PROCESSED, USE THIS AS THE FIRST PLUGIN

    """

    def register(self):
        self.available_args["source"] = "source for VideoSource (int for camera index, filename for video file, or pattern 'data/{num}.png' for image sequence)"
        
        self.available_args["properties"] = "this should be a vpl.CameraProperties objects"
        self.available_args["repeat"] = "bool whether or not to repeat an image sequence (default is False)"


    def camera_update_image(self):
        self.camera_flag, self.camera_image = self.camera.read()

    def video_reader_update_image(self):

        if len(self.images) < 1 or self.images[-1] is not None:
            # we are still reading
            my_idx = self.images_idx

            _, _img = self.video_reader.read()

            if not _:
                self.images_idx = 0
                self.images += [None]
            else:
                self.images += [_img]
                self.camera_image = _img
                return

        if self.get("repeat", False):
            # looping back through them
            my_idx = self.images_idx

            my_idx = my_idx % (len(self.images) - 1)

            self.images_idx += 1

            self.camera_image = self.images[my_idx]
            return

        return False, None


    def image_sequence_update_image(self):
        my_idx = self.images_idx
        if self.get("repeat", False):
            my_idx = my_idx % len(self.images)
        self.images_idx += 1

        if my_idx >= len(self.images):
            return False, None

        if self.images[my_idx] is None:
            self.images[my_idx] = cv2.imread(self.image_sequence_sources[my_idx])

        self.camera_image = self.images[my_idx]

    def update_image(self):
        stime = time.time()

        if self._type == "video":
            self.video_reader_update_image()
        elif self._type == "sequence":
            self.image_sequence_update_image()
        elif self._type == "camera":
            self.camera_update_image()

        self.camera_image = self.camera_image

        etime = time.time()
        elapsed_time = etime - stime
        self.update_fps = 1.0 / elapsed_time if elapsed_time != 0 else -1.0


    def update_cap_props(self):

        if self._type == "video":
            self.cap_fps = self.video_reader.get(vpl.defines.cap_prop_lookup["FPS"])
        elif self.get("cap_fps", None) is not None:
            self.cap_fps = self.get("cap_fps", None)
        

    def update_loop(self):
        while True:
            try:
                st = time.time()
                self.update_image()
                et = time.time()
                dt = et - st
                self.camera_fps = 1.0 / dt if dt > 0 else 0

                if self.cap_fps is not None and self.cap_fps > 0:
                    if dt > 0 and dt < 1.0 / self.cap_fps:
                        time.sleep(1.0 / self.cap_fps - dt)
                
            except:
                pass

    def set_camera_props(self):
        props = self["properties"]
        if props != None:
            for p in props.props:
                #print ("setting: " + str(cap_prop_lookup[p]) + " to: " + str(type(props[p])))
                if p not in cap_prop_lookup.keys():
                    raise Exception("Unknown camera property: '%s'" % p)
                self.camera.set(cap_prop_lookup[p], props[p])

    def get_image(self):
        if not self.is_async:
            st = time.time()
            self.update_image()
            et = time.time()
            dt = et - st
            self.camera_fps = 1.0 / dt if dt > 0 else 0

        return self.camera_image

    def process(self, pipe, image, data):
        if not hasattr(self, "has_init"):
            # first time running, default camera
            self.has_init = True

            # default async is false
            self.is_async = self.get("is_async", False)

            source = self.get("source", 0)

            self._source = source

            # default images
            self.camera_flag, self.camera_image = True, np.zeros((320, 240, 3), np.uint8)

            if isinstance(source, int) or source.isdigit():
                if not isinstance(source, int):
                    source = int(source)
                # create camera
                self.camera = cv2.VideoCapture(source)
                self.set_camera_props()

                self._type = "camera"

            elif isinstance(source, str):
                _, extension = os.path.splitext(source)
                extension = extension.replace(".", "").lower()


                if extension in vpl.defines.valid_image_formats:
                    # have an image sequence
                    self.image_sequence_sources = glob.glob(source)

                    self._type = "sequence"

                    self.images_idx = 0
                    self.images = [None] * len(self.image_sequence_sources)

                elif extension in vpl.defines.valid_video_formats:
                    # read from a video file
                    self.video_reader = cv2.VideoCapture(source)
                    self._type = "video"
                    self.images_idx = 0

                    self.images = []
                else:
                    raise Exception("unknown source type:" + str(source))

            else:
                # use an already instasiated camera
                self.camera = source
                self.set_camera_props()
                self._type = "camera"

            self.update_cap_props()

            for i in range(self.get("burn", 0)):
                self.update_image()

            if self.is_async:
                self.do_async(self.update_loop)


            #while not hasattr(self, "has_loop"):
            #    time.sleep(0.1)

        image = self.get_image()

        #data["camera_flag"] = flag
        if hasattr(self, "camera_fps"):
            data["camera_" + str(self._source) + "_fps"] = self.camera_fps

        if hasattr(self, "cap_fps") and self.cap_fps is not None and self.cap_fps > 0:            
            data["cap_fps"] = self.cap_fps
        
        if image is None:
            pipe.quit()

        return image, data




class VideoSaver(VPL):
    """

    Usage: VideoSaver(path="data/{num}.png")

      * "path" = image format, or video file (.mp4 or .avi)


    optional arguments:
    
      * "every" = save every N frames (default 1 for every frame)

    Saves images as they are received to their destination

    """

    def register(self):
        self.available_args["path"] = "string path like (data/{num}.png) or video file like (data/mine.mp4)"
        self.available_args["every"] = "integer number of saving one every N frames (default is 1, every frame)"
        self.available_args["fps"] = "frames per second to write to video file(default 24)"

    def end(self):
        if hasattr(self, "video_out"):
            self.video_out.release()


    def save_image(self, image, num):
        #print ('saving ' + str(num))
        if self._type == "video":
            if (not hasattr(self, "last_time") or time.time() - self.last_time >= 1.0 / self.fps) or (not self.is_async):
                #self.video_proc.stdin.write(image.tostring())
                #image.save(self.video_proc.stdin, "PNG")

                #r = cv2.imencode(".png", image)[1]

                self.video_proc.stdin.write(image.tostring())
                self.video_proc.stdin.flush()

                #self.video_out.write(image)
                self.last_time = time.time()

        elif self._type == "sequence":
            
            loc = pathlib.Path(self["path"].format(num="%08d" % num))

            cv2.imwrite(str(loc), image)

        self.saved_nums += [num]

    def save_image_loop(self):
        while True:
            m_num = max(self.saved_nums, default=-1)

            for i in range(len(self.pending_images)):
                if self.pending_images[i][1] == m_num + 1:
                    print ("saving " + str(self.pending_images[i][1]))
                    self.save_image(self.pending_images[i][0], self.pending_images[i][1])
                    del self.pending_images[i]
                    break


    def process(self, pipe, image, data):
        if not hasattr(self, "num"):
            self.num = 0

            self.saved_nums = []
            self.pending_images = []

            self.is_async = False#self.get("is_async", True)

            _, ext = os.path.splitext(self["path"])
            if ext.replace(".", "").lower() in vpl.defines.valid_video_formats:
                self._type = "video"

                h, w, d = image.shape
                #cc_text = self.get("fourcc", "H264")
                cc_text = None
                
                #cc_text = self.get("fourcc", "3IVD")

                cc_text = self.get("fourcc", "DIVX")#"3IVD")#"DIB ")#"FFV1")

                self.fourcc = cv2.VideoWriter_fourcc(*cc_text)


                if self.get("fps", None) is not None:
                    self.fps = self["fps"]
                elif "cap_fps" in data.keys():
                    self.fps = data["cap_fps"]
                else:
                    self.fps = self.get("fps", 24)                    
                
                loc = pathlib.Path(self["path"])
                if not loc.parent.exists():
                    loc.parent.mkdir(parents=True)

                cmd = ['ffmpeg', '-y', 
                    '-f', 'rawvideo',
                    '-s', '%dx%d' % (w, h),
                    '-vcodec', 'rawvideo',
                    '-pix_fmt', 'bgr24',
                    '-r', str(self.fps),
                    '-i', '-',

                    '-an',
                    
                    '-vcodec', self.get("vcodec", 'h264'),
                    '-b:v', self.get("kbps", '30000k'),
                    #'-qscale', '5',
                    '-r', str(self.fps),

                    self["path"]
                ]

                #print (" ".join(cmd))
                self.video_proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

                # using opencv
                #self.video_out = cv2.VideoWriter(self["path"], self.fourcc, self.fps, (w, h))
                

            else:
                self._type = "sequence"
                
                _loc = pathlib.Path(self["path"])

                if not _loc.parent.exists():
                    _loc.parent.mkdir(parents=True)

            if self.is_async:
                self.do_async(self.save_image_loop, ())
        
        if self.num % self.get("every", 1) == 0:

            # async save it
            if self.is_async:
                self.pending_images += [(image.copy(), self.num)]
            else:
                self.save_image(image.copy(), self.num)

        self.num += 1

        return image, data


class Display(VPL):
    """

    Usage: Display(title="mytitle")

        * "title" = the window title

    """

    def register(self):
        self.available_args["title"] = "opencv window title"

    def process(self, pipe, image, data):

        if not hasattr(self, "is_init"):
            cv2.namedWindow(self["title"])
            self.is_init = True
            
        cv2.imshow(self["title"], np.abs(image))

        cv2.waitKey(1)

        if cv2.getWindowProperty(self["title"], cv2.WND_PROP_VISIBLE) <= 0:
            pipe.quit()

        return image, data
