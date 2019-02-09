"""

fun filters

"""

from vpl import VPL

import cv2
import numpy as np

import math
import random

class CoolChannelOffset(VPL):

    def register(self):
        pass

    def process(self, pipe, image, data):
        h, w, nch = image.shape

        #offset_gen = self.get("offset", lambda i: i * (8, -2.5))
        offset_gen = lambda i: (8 * i, -2.5 * i)
        for i in range(nch):
            offset = offset_gen * i if type(offset_gen) in (tuple, list) else offset_gen(i)
            image[:,:,i] = np.roll(np.roll(image[:,:,i], int(offset[1]), 0), int(offset[0]), 1)

        return image, data


class Diff(VPL):

    def process(self, pipe, image, data):

        ret = None

        if not hasattr(self, "last_image"):
            ret = image
        else:
            ret = cv2.absdiff(image.copy(), self.last_image.copy())
            gray = cv2.cvtColor(ret, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(gray, 2, 255, cv2.THRESH_BINARY)

            real = cv2.bitwise_and(image.copy(), image.copy(), mask = mask)

            ret = real

        self.last_image = image.copy()

        return ret, data


class Bleed(VPL):

    def process(self, pipe, image, data):
        N = self.get("N", 18)
        if not hasattr(self, "buffer"):
            self.buffer = []

        arith_dtype = np.float32

        self.buffer.insert(0, image.astype(arith_dtype))

        if len(self.buffer) >= N:
            self.buffer = self.buffer[:N]

        #a = [len(self.buffer) - i + N for i in range(0, len(self.buffer))]
        a = [(N - i) * 2.0 for i in range(0, len(self.buffer))]

        # normalize
        a = np.array([a[i] / sum(a) for i in range(len(a))], dtype=arith_dtype)

        b4dtype = image.dtype

        image = image.copy().astype(arith_dtype)

        image[:,:,:] = 0
        
        h, w, d = image.shape

        for i in range(len(a)):
            if image.shape != self.buffer[i].shape:
                self.buffer[i] = cv2.resize(self.buffer[i], (w, h))

            #image = image + a[i] * self.buffer[i]
            image = cv2.addWeighted(image, 1.0, self.buffer[i], a[i], 0)

        return image.astype(b4dtype), data

        """

        b4dtype = image.dtype
        image = image.astype(np.float32)

        for i in range(len(a)):
            image = image + self.buffer[i] * a[i]

        return image.astype(b4dtype), data


        """



class Pixelate(VPL):

    def process(self, pipe, image, data):
        N = self.get("N", 7.5)

        h, w, d = image.shape

        image = cv2.resize(image, (int(w // N), int(h // N)), interpolation=cv2.INTER_NEAREST)
        image = cv2.resize(image, (w, h), interpolation=cv2.INTER_NEAREST)

        return image, data

class Noise(VPL):

    def process(self, pipe, image, data):
        level = self.get("level", .125)

        m = (100,100,100) 
        s = (100,100,100)
        noise = np.zeros_like(image)

        image = cv2.addWeighted(image, 1 - level, cv2.randn(noise, m, s), level, 0)

        return image, data


class DetailEnhance(VPL):

    def process(self, pipe, image, data):
        image = cv2.detailEnhance(image, sigma_s=self.get("r", 10), sigma_r=self.get("s", .15))
        return image, data


class Cartoon(VPL):

    def process(self, pipe, image, data):
        down = self.get("down", 2)
        bilateral = self.get("bilateral", 7)

        for i in range(down):
            image = cv2.pyrDown(image)

        for i in range(bilateral):
            image = cv2.bilateralFilter(image, d=9,
                                    sigmaColor=9,
                                    sigmaSpace=7)

        for i in range(down):
            image = cv2.pyrUp(image)

        image_gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        image_blur = cv2.medianBlur(image_gray, 7)

        image_edge = cv2.adaptiveThreshold(image_blur, 255,
                                 cv2.ADAPTIVE_THRESH_MEAN_C,
                                 cv2.THRESH_BINARY,
                                 blockSize=9,
                                 C=2)

        image_edge = cv2.cvtColor(image_edge, cv2.COLOR_GRAY2RGB)
        image_cartoon = cv2.bitwise_and(image, image_edge)

        return image_cartoon, data

class HSLBin(VPL):

    def process(self, pipe, image, data):
        hls_image = cv2.cvtColor(image, cv2.COLOR_BGR2HLS)

        def nearest(b, m):
            return m * (b // m)

        hls_image[:,:,0] = nearest(hls_image[:,:,0], self.get("H", 40))
        hls_image[:,:,1] = nearest(hls_image[:,:,1], self.get("L", 30))
        hls_image[:,:,2] = nearest(hls_image[:,:,2], self.get("S", 40))


        res_image = cv2.cvtColor(hls_image, cv2.COLOR_HLS2BGR)

        return res_image, data

class RainbowCrazy(VPL):

    def process(self, pipe, image, data):
        hls_image = cv2.cvtColor(image, cv2.COLOR_BGR2HLS)

        if not hasattr(self, "ct"):
            self.ct = 0

        hls_image[:,:,0] = ((hls_image[:,:,0] + self.ct * 3.5) % 180).astype(hls_image.dtype)
        #hls_image[:,:,2] += 20

        self.ct += 1

        res_image = cv2.cvtColor(hls_image, cv2.COLOR_HLS2BGR)

        return res_image, data

class Scanlines(VPL):

    def process(self, pipe, image, data):

        h, w, d = image.shape

        res = np.zeros(image.shape, dtype=image.dtype)

        if not hasattr(self, "ct"):
            self.ct = 0

        rnd_prd = random.random() * self.get("randomness", 0.0)

        for i in range(h):
            prd = rnd_prd + self.ct * self.get("speed", .8) / 60.0 + i * self.get("frequency", 1.6) / h
            off = self.get("size", 1.2) * math.tan(math.pi * prd)

            res[i] = np.roll(image[i], int(off), 0)

        self.ct += 1

        return res, data


class Roll(VPL):

    def register(self):
        self.available_args["h"] = "should be (lambda height, frame_count) to tell how much to roll"
        self.available_args["w"] = "should be (lambda width, frame_count) to tell how much to roll"

    def process(self, pipe, image, data):

        h, w, d = image.shape

        res = np.zeros(image.shape, dtype=image.dtype)

        if not hasattr(self, "ct"):
            self.ct = 0

        # check these out
        h_off = self.get("h", lambda height, frame_count: 0)
        w_off = self.get("w", lambda height, frame_count: 0)

        for i in range(h):
            off = h_off(i, self.ct)
            res[i] = np.roll(image[i], int(off), 0)

        image = res.copy()

        for i in range(w):
            off = w_off(i, self.ct)
            res[:,i,:] = np.roll(image[:,i,:], int(off), 0)

        self.ct += 1

        return res, data




class Grid(VPL):

    def register(self):
        self.available_args["h"] = "how many copies height wise"
        self.available_args["w"] = "how many copies width wise"
        self.available_args["keep_size"] = "whether or not to keep the input size (default True)"

    def process(self, pipe, image, data):

        h, w, d = image.shape

        orig_h, orig_w = int(h), int(w)


        # check these out
        h = self.get("h", 2)
        w = self.get("w", 2)

        if self.get("keep_size", True):
            image = cv2.resize(image.copy(), (orig_w // w, orig_h // h), cv2.INTER_NEAREST)

        res = image.copy()


        for i in range(h - 1):
            res = np.concatenate((res, image), axis=0)

        image = res.copy()

        for i in range(w - 1):
            res = np.concatenate((res, image), axis=1)

        if self.get("keep_size", True):
            res = cv2.resize(res, (orig_w, orig_h), cv2.INTER_NEAREST)

        return res, data




class EdgeDiff(VPL):

    def register(self):
        pass

    def process(self, pipe, image, data):
        if not hasattr(self, "roll"):
            self.roll = Roll(w=lambda a, b: 1, h=lambda a, b: 1)

        h, w, d = image.shape

        res, _ = self.roll.process(pipe, image, data)

        res = cv2.add(cv2.subtract(res, image), cv2.subtract(image, res))

        return res, data



class Transform(VPL):

    def register(self):
        pass

    def process(self, pipe, image, data):
        h, w, d = image.shape

        func = self.get("func", lambda x, y, w, h: (x, y))
        # ex: func=lambda x, y, w, h: (w * np.log(x+1) / np.log(w), h * np.log(y+1) / np.log(h))
        # this does log transofmr
        # ex: func=lambda x, y, w, h: (x , )

        map_x, map_y = np.fromfunction(lambda y, x: func(x, y, w, h), (h, w), dtype=np.float32)

        res = cv2.remap(image.copy(), map_x, map_y, cv2.INTER_LINEAR)

        return res, data



class Glitcher(VPL):

    """

    For randomly adding glitches

    """

    def register(self):
        pass


    def process(self, pipe, image, data):

        if not hasattr(self, "is_init"):
            self.is_init = True
            self.h_off = None
            self.w_off = None

        h, w, d = image.shape

        hseed = random.random()
        wseed = random.random()

        fc = .24

        hchance = 0.1 * fc if self.h_off is None else .4 * fc
        wchance = 0.08 * fc if self.w_off is None else .38 * fc

        if hseed < hchance:
            if self.h_off is None:
                self.h_off = random.randint(-h // 3, h // 3)
            else:
                self.h_off = None

        if wseed < wchance:
            if self.w_off is None:
                self.w_off = random.randint(-w // 3, w // 3)
            else:
                self.w_off = None


        if self.h_off is not None:
            image = np.roll(image, self.h_off, 1)


        if self.w_off is not None:
            image = np.roll(image, self.w_off, 0)

        return image, data



class Darken(VPL):

    """

    For darkening an image

    """

    def register(self):
        pass


    def process(self, pipe, image, data):
        h, w, d = image.shape

        fac = self.get("fac", .8)

        image = (image.astype(np.float32) * fac).astype(np.uint8)

        return image, data


class Threshold(VPL):

    """

    For darkening an image

    """

    def register(self):
        pass


    def process(self, pipe, image, data):
        h, w, d = image.shape

        threshold = self.get("threshold", 0.1)

        nimg = image.astype(np.float32)

        image[nimg < threshold * 255] = 0

        return image, data

















