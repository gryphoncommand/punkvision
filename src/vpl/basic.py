"""

basic operations

"""

from vpl import VPL

import numpy as np

import math

import cv2

import time

import scipy as sp
from scipy import signal, ndimage

class Resize(VPL):
    """

    Usage: Resize(size=(w, h))

      * "w" = width, in pixels
      * "h" = height, in pixels

    optional arguments:

      * "method" = opencv resize method, default is cv2.INTER_LINEAR

    """

    def register(self):
        self.available_args["w"] = "width in pixels"
        self.available_args["h"] = "height in pixels"

    def process(self, pipe, image, data):
        h_in, w_in, _= image.shape
        w_out, h_out = self.get("size", (None, None))

        # if one is 'None', replace it with the preexisting
        if w_out is None: w_out = w_in
        if h_out is None: h_out = h_in

        if w_out == w_in and h_out == h_in:
            # if it is the correct size, don't spend time resizing it
            return image, data
        else:
            resize_method = self.get("method", cv2.INTER_CUBIC)
            #t = cv2.UMat(image)
            r = cv2.resize(image, (w_out, h_out), interpolation=resize_method)
            return r, data


class Blur(VPL):
    """

    Usage: Blur(kernel=(w=5, h=5))

      * "w" = width, in pixels (for guassian blur, w % 2 == 1) (for median blur, this must be an odd integer greater than 1 (3, 5, 7... are good))
      * "h" = height, in pixels (for guassian blur, w % 2 == 1) (for median blur, this is ignored)

    optional arguments:

      * "method" = opencv blur method
      * "sx" = 'sigma x' for the Gaussian blur standard deviation, defaults to letting OpenCV choose based on image size
      * "sy" = 'sigma y' for the Gaussian blur standard deviation, defaults to letting OpenCV choose based on image size

    """

    def register(self):
        self.available_args["kernel"] = "width, height in pixels for blur kernel (for median blur, only width is used)"

        self.available_args["method"] = "method of blurring, 'box', 'median', 'guassian' are all good"

        self.available_args["sigma"] = "sigma x, y (guassian only)"


    def process(self, pipe, image, data):
        w_k, h_k = self.get("kernel", (0, 0))
        if w_k in (0, None) or h_k in (0, None):
            return image, data
        else:
            resize_method = self.get("method", "box")

            if resize_method == "guassian":
                sx, sy = self.get("sigma", (0, 0))
                return cv2.GaussianBlur(image, (w_k, h_k), sigmaX=sx, sigmaY=sy), data
            elif resize_method == "median":
                return cv2.medianBlur(image, w_k), data
            else:
                # default is box blur type
                return cv2.blur(image, (w_k, h_k)), data


class Bilateral(VPL):
    def register(self):
        pass

    def process(self, pipe, image, data):
        s_color = self.get("s_color", 8)
        s_space = self.get("s_space", 16)
        res = cv2.bilateralFilter(image.copy(), s_color, s_space, s_space)
        return res, data



class ConvertColor(VPL):
    """
    Usage: ConvertColor(conversion=None)
      * conversion = type of conversion (see https://docs.opencv.org/3.1.0/d7/d1b/group__imgproc__misc.html#ga4e0972be5de079fed4e3a10e24ef5ef0) ex: cv2.COLOR_BGR2HSL
    """

    def process(self, pipe, image, data):
        if self["conversion"] is None:
            return image, data
        else:
            return cv2.cvtColor(image, self["conversion"]), data


class FPSCounter(VPL):
    """

    Usage: FPSCounter()


    Simply adds the FPS in the bottom left corner

    """

    def register(self):
        pass

    def process(self, pipe, image, data):
        if not hasattr(self, "fps_records"):
            self.fps_records = []

        if not hasattr(self, "last_print"):
            self.last_print = (0, None)

        ctime = time.time()
        self.fps_records += [(ctime, pipe.chain_fps[0])]
        
        # filter only the last second of readings
        self.fps_records = list(filter(lambda tp: abs(ctime - tp[0]) < 1.0, self.fps_records))

        avg_fps = sum([fps for t, fps in self.fps_records]) / len(self.fps_records)

        if self.last_print[1] is None or abs(ctime - self.last_print[0]) > 1.0 / 3.0:
            self.last_print = (ctime, avg_fps)


        font = cv2.FONT_HERSHEY_SIMPLEX
        height, width, _ = image.shape
        geom_mean = math.sqrt(height * width)
        offset = geom_mean * .01
        
        return cv2.putText(image.copy(), "%2.1f" % self.last_print[1], (int(offset), int(height - offset)), font, offset / 6.0, (255, 0, 0), int(offset / 6.0 + 2)), data




class Grayscale(VPL):
    """


    """

    def register(self):
        pass

    def process(self, pipe, image, data):
        r, g, b = image[:,:,0], image[:,:,1], image[:,:,2]
        atype = np.float32
        bw = ((r.astype(atype) + g.astype(atype) + b.astype(atype)) / 3.0).astype(image.dtype)

        for i in range(0, 3):
            image[:,:,i] = bw
        return image, data




class PrintInfo(VPL):

    def register(self):
        self.available_args["fps"] = "fps cap to display results at"

    def process(self, pipe, image, data):
        if not hasattr(self, "num"):
            self.num = 0
        if not hasattr(self, "last_time") or time.time() - self.last_time > 1.0 / self.get("fps", 3):
            if self.get("extended", False):
                print ("(#%d) image[%s]: %s" % (self.num, image.dtype, image.shape))
                
                print ("total fps: %.1f" % (pipe.chain_fps[0]))
                for i in range(len(pipe.chain)):
                    if i < len(pipe.chain_fps[1]):
                        print ("  %s # %.1f fps" % (str(pipe.chain[i]), pipe.chain_fps[1][i]))
                    else:
                        print ("  %s" % (str(pipe.chain[i])))

                print ("data: ")
                
                for k in data:
                    print ("  %s: %s" %(k, data[k]))

                print("")

            else:
                print ("image[%s]: %s" % (image.dtype, image.shape))
                print ("fps: %s" % str(pipe.chain_fps))

            print("")

            self.last_time = time.time()

        self.num += 1

        return image, data


class Erode(VPL):
    """

    Usage: Erode(mask, None, iterations) 
    
    """
    def process(self, pipe, image, data):
        image = cv2.erode(image, None, iterations=self.get("iterations", 2))
        return image, data

class Dilate(VPL):
    """

    Usage: Dilate(mask, None, iterations)

    """
    def process(self, pipe, image, data):
        image = cv2.dilate(image, None, iterations=self.get("iterations", 2))
        return image, data


class Distort(VPL):
    """

    Usage: Dilate(mask, None, iterations)

    """
    def process(self, pipe, image, data):
        image = image.astype(np.float32) / 255.0
        image = image * 7.5
        return (255 * image).astype(np.uint8), data




class Convolve(VPL):
    
    def register(self):
        pass

    def process(self, pipe, image, data):
        kernel = self.get("scale", 1.0) * np.array(self.get("kernel", [[1]]), dtype=np.float32)
        for d in range(3):
            image[:,:,d] = (256.0 * np.clip(sp.ndimage.convolve(image[:,:,d] / 256.0, kernel, mode='constant', cval=0.0), 0.0, 1.0)).astype(np.uint8)
        return image, data


class OpenCLConvolve(VPL):

    def register(self):
        pass


    def process(self, pipe, image, data):
        import pyopencl as cl

        if not hasattr(self, "is_init"):
            # loop unrolling on mask
            mask = np.array(self.get("kernel", [[0, 0, 0], [0, 1, 0], [0, 0, 0]])) * self.get("factor", 1.0)
            
            if mask.shape[0] != mask.shape[1]:
                print ("WARNING: mask should be square for convolution!")

            if mask.shape[0] % 2 != 1:
                print ("WARNING: mask should be an odd length")

            single_val_codeblock = """
            tx = x + {i};
            ty = y + {j};
            if (tx >= 0 && tx < w && ty >= 0 && ty < h) {{
                tidx = tx + ty * w;
                c = (float)({MASK_VAL});
                nR += c * (float)img_in[3*tidx+0];
                nG += c * (float)img_in[3*tidx+1];
                nB += c * (float)img_in[3*tidx+2];
            }}
            """

            kernel_unfolded = ""

            for i in range(0, mask.shape[0]):
                for j in range(0, mask.shape[1]):
                    if mask[j, i] != 0:
                        cur_cb = single_val_codeblock.format(i=i - mask.shape[0] // 2, j=mask.shape[0] // 2 - j, MASK_VAL=mask[j, i])
                        kernel_unfolded += cur_cb

            #print (kernel_unfolded)

            OPENCL_SRC="""
__kernel void convert(__global __read_only uchar * img_in, __global __write_only uchar * img_out, int w, int h) {{
        int x = get_global_id(0), y = get_global_id(1);
        if (x >= w || y >= h) return;
        int idx = x + y * w;
        // img_in[3*idx+0] = R component at pixel x, y
        // img_in[3*idx+1] = G component at pixel x, y
        // img_in[3*idx+2] = B component at pixel x, y

        // new components
        float nR = 0, nG = 0, nB = 0;

        int tx, ty, tidx;
        float c;

        // AUTOGEN START

        {gen_code}

        // AUTOGEN END

        

        img_out[3 * idx + 0] = (uchar)clamp(nR, 0.0f, 255.0f);
        img_out[3 * idx + 1] = (uchar)clamp(nG, 0.0f, 255.0f);
        img_out[3 * idx + 2] = (uchar)clamp(nB, 0.0f, 255.0f);
    }}
""".format(gen_code=kernel_unfolded)

            #print(OPENCL_SRC)

            mf = cl.mem_flags

            platform = cl.get_platforms()[self.get("opencl_platform", 0)]
            devs = platform.get_devices()[self.get("opencl_device", -1)]
            self.ctx = cl.Context(devs if isinstance(devs, list) else [devs])
            self.queue = cl.CommandQueue(self.ctx)

            # now build the programs
            self.prg = cl.Program(self.ctx, OPENCL_SRC).build()

            self.src_buf = cl.Buffer(self.ctx, mf.READ_ONLY, image.nbytes)
            self.dest_buf = cl.Buffer(self.ctx, mf.WRITE_ONLY, image.nbytes)
            self.dest = np.empty_like(image)

            # we have initialized
            self.is_init = True

        h, w, _ = image.shape

        # write current image
        cl.enqueue_copy(self.queue, self.src_buf, image)

        self.prg.convert(self.queue, (w, h), None, self.src_buf, self.dest_buf, np.int32(w), np.int32(h))
        
        # read back image
        cl.enqueue_copy(self.queue, self.dest, self.dest_buf)

        return self.dest, data


