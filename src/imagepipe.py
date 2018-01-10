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


import os
import time
import threading
import traceback

import cv2
import numpy

import pmath

import imagestream
import glob


class ImagePipe():
    def __init__(self, args, imageHandle=None):
        self.imageHandle = imageHandle
        self.args = args

        self.center = pmath.Pt((-1, -1))
        self.contours = []
        self.fitness = -float('inf')

        self.inputType = ""

        self.im = {
            "input": None,
            "output": None,
        }

        self.threads = { 
            "input": threading.Thread(target=self.__thread_input),
            "proc": threading.Thread(target=self.__thread_proc),
            "output": threading.Thread(target=self.__thread_output),
        }

        self.fps = dict({
            "input": -1,
            "output": -1,
            "proc": -1,
        })

        self.__get_num = 0
        self.__save_num = 0
        self.__total_save_num = 0

        if self.args.source.startswith("/dev/video"):
            l_int = len(self.args.source) - 1
            while l_int >= 0 and self.args.source[l_int].isdigit():
                l_int -= 1

            self.inputType = "cam"
            self.__camera_index = int(self.args.source[l_int+1:])
            self.__camera = cv2.VideoCapture(self.__camera_index)

            self.__camera.set(3, self.args.size[0])
            self.__camera.set(4, self.args.size[1])
            
            cmd = "v4l2-ctl -d /dev/video{0} -c exposure_auto=1 -c exposure_absolute={1}".format(self.__camera_index, self.args.exposure)
            os.system(cmd)
            time.sleep(.125)

        elif args.source is not None:
            self.__input_files = glob.glob(self.args.source)
            self.inputType = "dir"
        
        self.__has_printed = {
            "resize": False,
            "num": False,
        }

        if self.args.save is not None:
            mkd = self.args.save.split("/")[0]
            if not os.path.exists(mkd):
                os.makedirs(mkd)

        if args.stream is not None:
            imagestream.pipe = self
            self.stream = imagestream.ThreadedHTTPServer(('0.0.0.0', self.args.stream), imagestream.StreamHandle)
            pthread = threading.Thread(target=self.stream.serve_forever)
            pthread.start()


    def start(self):
        for thread in self.threads:
            self.threads[thread].start()

    def __thread_input(self):
        stime, etime = (0, 0)
        dtime  = 0
        while True:
            try:
                stime = time.time()
                self.__update_input()
                etime = time.time()
                self.fps["input"] = pmath.elapsed_fps(stime, etime)
                if self.args.fps:
                    dtime = (1.0 / self.args.fps) - (etime - stime)
                    if dtime > 0 and self.args.fps != None and self.inputType != "cam":
                        time.sleep(dtime)
            except Exception as e:
                print(str(e))
                traceback.print_exc()
                pass

    def __thread_output(self):
        if self.args.save in (False, None):
            return
        stime, etime = (0, 0)
        dtime  = 0
        while True:
            try:
                stime = time.time()
                if not self.args.save in (False, None):
                    self.__save_im()
                etime = time.time()
                self.fps["output"] = pmath.elapsed_fps(stime, etime)
                if self.args.fps:                
                    dtime = (1.0 / self.args.fps) - (etime - stime)
                    if dtime > 0 and self.args.fps != None:
                        time.sleep(dtime)
            except Exception as e:
                print(str(e))
                traceback.print_exc()
                pass
        
    def __thread_proc(self):
        stime, etime = (0, 0)
        dtime  = 0
        while True:
            try:
                stime = time.time()
                self.process()
                if self.imageHandle is not None:
                    self.imageHandle(self)
                self.fps["proc"] = pmath.elapsed_fps(stime, etime)
                etime = time.time()
                if self.args.fps:
                    dtime = (1.0 / self.args.fps) - (etime - stime)
                    if dtime > 0 and self.args.fps != None:
                        time.sleep(dtime)
            except Exception as e:
                print(str(e))
                traceback.print_exc()
                pass


    def __print_once(self, title, msg):
        if title not in self.__has_printed or not self.__has_printed[title]:
            print (msg)
            self.__has_printed[title] = True

    def __update_input(self):
        if self.inputType == "cam":
            retval, self.im["input"] = self.__camera.read()
        elif self.inputType == "dir":
            if self.__get_num < len(self.__input_files):
                self.im["input"] = cv2.imread(self.__input_files[self.__get_num])
            else:
                self.__print_once("input", "input ran out")
            self.__get_num += 1

    def __fitness_contours(self, contours):
        if len(contours) < 1:
            return
        fit = 0
        try:
            centers = [pmath.Pt(c) for c in contours]
            areas = [cv2.contourArea(c) for c in contours]
        except:
            traceback.print_exc()
            return fit

        X = numpy.array([center.v[0] for center in centers])
        Y = numpy.array([center.v[1] for center in centers])
        AREA = numpy.array(areas)

        for i in self.args.fit.keys():
            fit += self.args.fit[i].func(self.args.size, X, Y, AREA)
            #print (fit)

        """
        if "dx" in self.args.fit.keys():
            avgx = sum([center.X for center in centers]) / float(len(centers))
            avgdx = sum([abs(center.X - avgx) for center in centers]) / float(len(centers))
            fit += self.args.fit["dx"] * avgdx
        if "dy" in self.args.fit.keys():
            avgy = sum([center.Y for center in centers]) / float(len(centers))
            avgdy = sum([abs(center.Y - avgy) for center in centers]) / float(len(centers))
            fit += self.args.fit["dy"] * avgdy
        if "da" in self.args.fit.keys():
            avga = sum([areas[i] for i in range(0, len(areas))]) / float(len(areas))
            avgda = sum([abs(areas[i] - avga) for i in range(0, len(areas))]) / float(len(areas))
            fit += self.args.fit["da"] * avgda

        # geometric average of areas
        if "qa" in self.args.fit.keys():
            avgqa = 1
            for area in areas:
                avgqa *= area ** (1.0 / len(areas))
            def __qa(a0, avg):
                ret = float(a0) / avg
                if ret < 1: ret = 1.0 / ret
                return ret

            avgda = sum([abs(areas[i] - avga) for i in range(0, len(areas))]) / float(len(areas))

            qa = float(area1) / area0
            if qa < 1:
                qa = 1.0 / qa
            fit += self.args.fit["qa"] * qa
        """

        return fit

    def get_best_fit(self, contours):
        num = self.args.num
        if num > len(contours):
            num = len(contours)
            self.__print_once("num", "Not enough contours found")
            return None
        max_indexes = tuple([-1] * num)
        max_fitness = -float('inf')
        import itertools
        for indexes in itertools.combinations(range(0, len(contours)), num):
            c_fit = self.__fitness_contours([contours[i] for i in indexes])
            if c_fit > max_fitness:
                max_fitness = c_fit
                max_indexes = tuple([i for i in indexes])
        if max_fitness == -float('inf') or -1 in max_indexes:
            return {
                "fitness": None,
                "contours": (None, ),
            }
        else:
            return {
                "fitness":  max_fitness,
                "contours": tuple([contours[i] for i in max_indexes]),
            }

    def __save_im(self):
        if not self.im["output"] is None and 0 not in self.im["output"].shape:
            if self.__total_save_num % self.args.save_every == 0:
                fmt = { 
                    "num": self.__save_num, 
                    "time": int(time.time() * 1000) 
                }
                cv2.imwrite(self.args.save.format(fmt["num"], fmt["time"], **fmt), self.im["output"])
                self.__save_num += 1
            self.__total_save_num += 1

    def process(self):
        if self.im["input"] is None:
            return
        im = self.im["input"].copy()
        height, width, depth = im.shape
        if (width, height) != self.args.size:
            self.__print_once("resize", "Image had to be manually resized from {0} to {1}".format((width, height), self.args.size))
            im = cv2.resize(im, self.args.size, interpolation=cv2.INTER_CUBIC)
            height, width, depth = im.shape
        im = cv2.cvtColor(im, cv2.COLOR_BGR2HLS)
        if self.args.D["reg"] not in (False, None):
            oversample = 5
            avgLuminance = (oversample ** 2) * numpy.sum(im[0:height:oversample,0:width:oversample,1]) / (height * width)
            im[::1] = numpy.multiply(im[::1], 100.0 / avgLuminance)
        if 0 not in self.args.blur:
            im = cv2.blur(im, self.args.blur)
        
        # filter images
        cvt_im = cv2.inRange(im, (self.args.H[0], self.args.L[0], self.args.S[0]),  (self.args.H[1], self.args.L[1], self.args.S[1]))
        if cv2.__version__.startswith("2"):
            raw_contours, _ = cv2.findContours(cvt_im, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)
        elif cv2.__version__.startswith("3"):
            _, raw_contours, _ = cv2.findContours(cvt_im, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)
        else:
            raise Exception("Dont know the opencv version: {0}".format(cv2.__version__))
        contours = []
        for i in range(0, len(raw_contours)):
            good = True

            for j in self.args.filter.keys():
                # x, y, area
                cntr = pmath.Pt(raw_contours[i])
                good = good and self.args.filter[j].func(self.args.size, cntr.X, cntr.Y, cv2.contourArea(raw_contours[i]))

                if not good:
                    break

            if good:
                contours.append(raw_contours[i])

        best_fit = self.get_best_fit(contours)
        if best_fit is not None:
            best_fitness = best_fit["fitness"]
            contours = best_fit["contours"]
            
            center = pmath.Pt((-1, -1))

            if best_fitness != None:
                centers = [pmath.Pt(c) for c in contours]
                areas = [cv2.contourArea(c) for c in  contours]

                center = pmath.Pt((0, 0))
                for _cen in centers:
                    center += _cen
                if len(centers) != 0:
                    center = center / float(len(centers))
                    if not self.args.D["draw"] in (False, None):
                        if not self.args.D["contour"] in (False, None):
                            for i in range(0, len(contours)):
                                cv2.drawContours(im, contours, i, self.args.D["contour"], self.args.D["contour-thickness"])
                        
                        if not self.args.D["contour-reticle"] in (False, None):
                            retcol = self.args.D["contour-reticle"]
                            retsize = self.args.D["contour-reticle-size"]
                            retthickness = self.args.D["contour-reticle-thickness"]
                            for j in range(0, len(centers)):
                                cv2.circle(im, centers[j].std(), retsize, retcol, retthickness)
                                offX = pmath.Pt((retsize, 0))
                                offY = pmath.Pt((0, retsize))
                                cv2.line(im, (centers[j] - offX).std(), (centers[j] + offX).std(), retcol, retthickness)
                                cv2.line(im, (centers[j] - offY).std(), (centers[j] + offY).std(), retcol, retthickness)

                        if not self.args.D["reticle"] in (False, None):
                            retcol = self.args.D["reticle"]
                            retsize = self.args.D["reticle-size"]
                            retthickness = self.args.D["reticle-thickness"]
                            cv2.circle(im, center.std(), retsize, retcol, retthickness)
                            offX = pmath.Pt((retsize, 0))
                            offY = pmath.Pt((0, retsize))
                            cv2.line(im, (center - offX).std(), (center + offX).std(), retcol, retthickness)
                            cv2.line(im, (center - offY).std(), (center + offY).std(), retcol, retthickness)

            self.center = center
            self.contours = contours
            self.fitness = best_fitness

        im = cv2.cvtColor(im, cv2.COLOR_HLS2BGR)


        self.im["output"] = im



