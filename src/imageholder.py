
import glob
import threading
import os
import itertools
import cv2
import time
import traceback
import pmath
import numpy


# this is a class to generate and hold images
class ImageHolder:

    def __init__(self, image_source, size, H, L, S, N_contours=1, exposure=None, fps_lim=None, save_input_pattern=None, save_output_pattern=None, filters={}, fitness={}, Dconfig={}, handler=None, save_every=1):
        """

        image_source can be "/dev/video[N]" to use a camera, or a glob pattern such as "files/*.png"

        """
        self.image_source = image_source

        self.save_input_pattern = save_input_pattern
        self.save_output_pattern = save_output_pattern
        self.size = size

        self.save_every = save_every

        self.Dconfig = Dconfig
        self.filters = filters
        self.fitness = fitness

        self.handler = handler

        self.H = H
        self.L = L
        self.S = S

        self.fps_lim = fps_lim

        self.N_contours = N_contours

        self.best_fitness = None
        self.best_group = None
        self.best_center = None

        self.__camera = None
        self.__images = None

        self.im = {
            "input": None,
            "output": None,
        }

        self.threads = { 
            "input": threading.Thread(target=self.__thread_base, args=(self.__update_input, "input")),
            "proc": threading.Thread(target=self.__thread_base, args=(self.process_image, "proc")),
            "output": threading.Thread(target=self.__thread_base, args=(self.output_image, "output")),
        }

        self.threads_time = {
            "input": None,
            "proc": None,
            "output": None,
        }

        self.last_ran = 0

        self.num_images = {
            "input": 0,
            "proc": 0,
            "output": 0,
        }

        self.fps = {
            "input": None,
            "proc": None,
            "output": None,
        }

        self.printed_things = set()

        if self.image_source.startswith("/dev/video"):
            cam_index = int(self.image_source.replace("/dev/video", ""))
            self.__camera = cv2.VideoCapture(cam_index)

            self.__camera.set(3, self.size[0])
            self.__camera.set(4, self.size[1])

            if exposure is not None:
                cmd = "v4l2-ctl -d /dev/video{0} -c exposure_auto=1 -c exposure_absolute={1}".format(cam_index, exposure)
                #os.system(cmd)
                #time.sleep(.125)
        elif type(self.image_source) == str:
            self.__images = glob.glob(self.image_source)

        if self.save_input_pattern is not None:
            mkd = self.save_input_pattern.split("/")[0]
            if not os.path.exists(mkd):
                os.makedirs(mkd)

        if self.save_output_pattern is not None:
            mkd = self.save_output_pattern.split("/")[0]
            if not os.path.exists(mkd):
                os.makedirs(mkd)

    # only prints things once, since it can get very annoying and cluttering
    def __print_once(self, msg):
        if msg not in self.printed_things:
            print (msg)
            self.printed_things.add(msg)


    def start(self):
        for thread in self.threads:
            self.threads[thread].start()

    def __update_input(self):
        if self.__camera is not None:
            st = time.time()
            retval, self.im["input"] = self.__camera.read()
            et = time.time()
            dt = et - st
            if dt > 0:
                self.fps["camread"] = 1.0 / dt

            self.num_images["input"] += 1
        elif self.__images is not None:
            self.im["input"] = cv2.imread(self.__images[self.num_images["input"] % len(self.__images)])
            self.num_images["input"] += 1
            
        self.last_ran = time.time()

    def get_contours(self, im):
        cvt_im = cv2.inRange(im, (self.H[0], self.L[0], self.S[0]),  (self.H[1], self.L[1], self.S[1]))

        st = time.time()
        _, raw_contours, _ = cv2.findContours(cvt_im, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)
        et = time.time()
 
        contours = []
        for i in range(0, len(raw_contours)):
            good = True

            for j in self.filters.keys():
                try:
                    center = pmath.Pt(raw_contours[i])
                    # img_size, x, y, area
                    good = good and self.filters[j].func(self.size, center.X, center.Y, cv2.contourArea(raw_contours[i]))

                except Exception as e:
                    print ("while executing defined filter '%s' (code: '%s'): %s" % (self.filters[j].name, self.filters[j].src, str(e)))

                if not good:
                    break

            if good:
                contours.append(raw_contours[i])

        return contours

    def get_fitness(self, contour_group):
        centers = [pmath.Pt(c) for c in contour_group]
        areas = [cv2.contourArea(c) for c in contour_group]

        X = numpy.array([center.v[0] for center in centers])
        Y = numpy.array([center.v[1] for center in centers])
        AREA = numpy.array(areas)

        total_fitness = 0.0

        for fit in self.fitness:
            # 
            try:
                fit_arr = self.fitness[fit].func(self.size, X, Y, AREA)
                if type(fit_arr) in (float, int):
                    total_fitness += fit_arr
                else:
                    total_fitness += sum(fit_arr)
            except Exception as e:
                print ("while executing fitness '%s' (src: '%s'): %s" % (fit, self.fitness[fit].src, str(e)))
        
        return total_fitness

    def get_best_fit(self, contours):
        max_fitness = None
        max_idxs = None
        for indexes in itertools.combinations(range(0, len(contours)), self.N_contours):
            c_fit = self.get_fitness([contours[i] for i in indexes])
            if max_fitness is None or c_fit > max_fitness:
                max_fitness = c_fit
                max_idxs = indexes
        if max_fitness is not None:
            return [contours[i] for i in max_idxs], max_fitness
        else:
            return None, None


    def process_image(self):
        if self.im["input"] is None:
            return
       # print ('start process')

        im = self.im["input"].copy()


        height, width, depth = im.shape
        if (width, height) != self.size:
            self.__print_once ("Image had to be manually resized from {0} to {1}".format((width, height), self.size))
            im = cv2.resize(im, self.size, interpolation=cv2.INTER_LANCZOS4)
            height, width, depth = im.shape



        im = cv2.cvtColor(im, cv2.COLOR_BGR2HLS)
        if self.Dconfig["normalize"] not in (False, None):
            oversample = 4
            avgLuminance = (oversample ** 2) * numpy.sum(im[0:height:oversample,0:width:oversample,1]) / (height * width)
            im[::1] = numpy.multiply(im[::1], 120.0 / avgLuminance)


        if self.Dconfig["blur"] is not None and 0 not in self.Dconfig["blur"]:
            im = cv2.blur(im, self.Dconfig["blur"])

        #print ('getting contours')

        contours = self.get_contours(im)


        #print ('getting best fit')
        
        best_group, best_fitness = self.get_best_fit(contours)

        #print('got it')

        # drawing
        if best_fitness != None:
            for i in range(0, len(best_group)):
                cv2.drawContours(im, best_group, i, self.Dconfig["contour"], self.Dconfig["contour-thickness"])



        # end drawing
        im = cv2.cvtColor(im, cv2.COLOR_HLS2BGR)

        self.best_group = best_group
        self.best_fitness = best_fitness
        if self.best_fitness is not None:
            best_centers = [pmath.Pt(c) for c in best_group]
            self.best_center = sum([i.v[0] for i in best_centers]) / len(best_group), sum([i.v[1] for i in best_centers]) / len(best_group)
        else:
            self.best_center = None


       # print ('end process')

        self.im["output"] = im

        self.num_images["proc"] += 1


    def output_image(self):
        if self.im["output"] is None:
            return

        im = self.im["output"].copy()

        if self.save_input_pattern is not None and self.num_images["output"] % self.save_every == 0:
            file_name = self.save_input_pattern.format(num=self.num_images["output"])
            cv2.imwrite(file_name, im)

        if self.save_output_pattern is not None and self.num_images["output"] % self.save_every == 0:
            file_name = self.save_output_pattern.format(num=self.num_images["output"])
            cv2.imwrite(file_name, im)

        #print (self.fps)

        self.handler(self)

        self.num_images["output"] += 1


    def __thread_base(self, method, name):
        my_last_ran = 0
        while True:
            try:
                if name != "input":
                    while self.last_ran == my_last_ran:
                        pass
                        #time.sleep(.01)
                my_last_ran = self.last_ran

                stime = time.time()
                method()
                etime = time.time()

                dtime = etime - stime
                if dtime == 0:
                    self.fps[name] = 1001
                else:
                    self.fps[name] = 1.0 / dtime

                if self.fps_lim:
                    ntime = (1.0 / self.fps_lim) - (etime - stime)
                    if ntime > 0 and self.fps_lim != None and self.__camera != None:
                        time.sleep(ntime)
            except Exception as e:
                print(str(e))
                traceback.print_exc()
                pass

