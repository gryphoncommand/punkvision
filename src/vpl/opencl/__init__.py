"""

OpenCL interface

"""

import vpl
import pyopencl as cl
mf = cl.mem_flags
import numpy as np


def create_system(code_src, platform=None, device=None):
    if platform is None:
        platform = 0

    platform = cl.get_platforms()[platform]

    if device is None:
        dev_list = platform.get_devices()[1]
    else:
        dev_list = platform.get_devices()[device]
    

    ctx = cl.Context(dev_list if isinstance(dev_list, list) else [dev_list])
    queue = cl.CommandQueue(ctx)

    prg = cl.Program(ctx, code_src).build()
    
    #print (platform, dev_list)
    #self.dest = np.empty_like(image)
    #self.src_buf = cl.Buffer(self.ctx, mf.READ_ONLY, image.nbytes)
    #self.dest_buf = cl.Buffer(self.ctx, mf.WRITE_ONLY, image.nbytes)
    
    return ctx, queue, prg


class ResizeCL(vpl.VPL):

    def register(self):
        
        self.ctx, self.queue, self.prg = create_system("""
// nearest neighbor
__kernel void resize_NN(
    __global __read_only uchar * img_in, int w_in, int h_in,
    __global __write_only uchar * img_out, int w_out, int h_out) {
    int x = get_global_id(0), y = get_global_id(1);
    if (x >= w_out || y >= h_out) return;
    
    int from_x = (x * w_in) / w_out, from_y = (y * h_in) / h_out;

    int idx_out = x + y * w_out, idx_in = from_x + from_y * w_in;

    img_out[3*idx_out+0] = img_in[3*idx_in+0];
    img_out[3*idx_out+1] = img_in[3*idx_in+1];
    img_out[3*idx_out+2] = img_in[3*idx_in+2];
}

    """)

        self.src_buf = None
        self.dest_buf = None
        self.dest = None

    def process(self, pipe, image, data):
        h_in, w_in, _ = image.shape
        w_out, h_out = self.get("size", (None, None))

        if w_out is None and h_out is None or (w_in == w_out and h_in == h_out):
            # no resizing neccessary
            return image, data
        else:
            if self.src_buf is None:
                self.src_buf = cl.Buffer(self.ctx, mf.READ_ONLY, image.nbytes)
            elif self.src_buf.size < image.nbytes:
                self.src_buf.release()
                self.src_buf = cl.Buffer(self.ctx, mf.READ_ONLY, image.nbytes)

            if self.dest is None:
                self.dest = np.zeros((h_out, w_out, 3), np.uint8)
                self.dest_buf = cl.Buffer(self.ctx, mf.WRITE_ONLY, self.dest.nbytes)
            elif self.dest.shape[0] < h_out or self.dest.shape[1] < w_out:
                self.dest = np.zeros((w_out, h_out, 3), np.uint8)
                self.dest_buf.release()
                self.dest_buf = cl.Buffer(self.ctx, mf.WRITE_ONLY, self.dest.nbytes)

            cl.enqueue_copy(self.queue, self.src_buf, image)

            self.prg.resize_NN(self.queue, (w_out, h_out), None, 
                self.src_buf, np.int32(w_in), np.int32(h_in), 
                self.dest_buf, np.int32(w_out), np.int32(h_out)
            )

            cl.enqueue_copy(self.queue, self.dest, self.dest_buf)

            return self.dest, data
            






class ConvolveCL(vpl.VPL):

    def register(self):

        #print (self.get("kernel"))

        def get_codeblock(i, j, kernel_val):
            # generates code for a single mask value and offset
            return """
            tx = x + """ + str(i) + """;
            ty = y + """ + str(j) + """;
            if (tx >= 0 && tx < w && ty >= 0 && ty < h) {
                tidx = tx + ty * w;
                c = (float)(""" + str(kernel_val) + """);
                nR += c * (float)img_in[3*tidx+0];
                nG += c * (float)img_in[3*tidx+1];
                nB += c * (float)img_in[3*tidx+2];
            }
            """
        
        kernel = self.get("scale", 1.0) * np.array(self.get("kernel", [[1]]))
                    
        if kernel.shape[0] % 2 != 1 or kernel.shape[1] % 2 != 1:
            print ("WARNING: mask should be (odd x odd) shape")

        generated_source = """
__kernel void convolve_HARDCODED(
    __global __read_only uchar * img_in, 
    __global __write_only uchar * img_out, int w, int h) {
    int x = get_global_id(0), y = get_global_id(1);
    if (x >= w || y >= h) return;
    int idx = x + y * w;

    // new components
    float nR = 0, nG = 0, nB = 0;

    int tx, ty, tidx;
    float c;

    // AUTOGEN START 
        """

        for i in range(0, kernel.shape[0]):
            for j in range(0, kernel.shape[1]):
                if kernel[j, i] != 0:
                    generated_source += get_codeblock(i - kernel.shape[0] // 2, kernel.shape[0] // 2 - j, kernel[j, i])

        generated_source += """

        // AUTOGEN END

        img_out[3 * idx + 0] = (uchar)floor(clamp(nR, 0.0f, 255.0f));
        img_out[3 * idx + 1] = (uchar)floor(clamp(nG, 0.0f, 255.0f));
        img_out[3 * idx + 2] = (uchar)floor(clamp(nB, 0.0f, 255.0f));
    }
        """


        self.ctx, self.queue, self.prg = create_system(generated_source)

        self.src_buf = None
        self.dest_buf = None
        self.dest = None

    def process(self, pipe, image, data):
        h, w, _ = image.shape

        if self.src_buf is None:
            self.src_buf = cl.Buffer(self.ctx, mf.READ_ONLY, image.nbytes)
        elif self.src_buf.size < image.nbytes:
            self.src_buf.release()
            self.src_buf = cl.Buffer(self.ctx, mf.READ_ONLY, image.nbytes)

        if self.dest is None:
            self.dest = np.zeros((h, w, 3), np.uint8)
            self.dest_buf = cl.Buffer(self.ctx, mf.WRITE_ONLY, self.dest.nbytes)
        elif self.dest.shape[0] < h or self.dest.shape[1] < w:
            self.dest = np.zeros((w, h, 3), np.uint8)
            self.dest_buf.release()
            self.dest_buf = cl.Buffer(self.ctx, mf.WRITE_ONLY, self.dest.nbytes)

        cl.enqueue_copy(self.queue, self.src_buf, image)

        self.prg.convolve_HARDCODED(self.queue, (w, h), None, 
            self.src_buf, 
            self.dest_buf, np.int32(w), np.int32(h)
        )

        cl.enqueue_copy(self.queue, self.dest, self.dest_buf)

        return self.dest, data
        




