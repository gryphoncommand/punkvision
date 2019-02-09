"""

for streaming things as a video

"""

from vpl import VPL

import time

from http.server import BaseHTTPRequestHandler,HTTPServer
from socketserver import ThreadingMixIn
import inspect

import cv2
import numpy as np


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

    def update_image(self, image):
        self.RequestHandlerClass.image = image

    def update_pipe(self, pipe):
        self.RequestHandlerClass.pipe = pipe

class MJPGStreamHandle(BaseHTTPRequestHandler):
    """

    handles web requests for MJPG

    """

    def do_GET_MJPG(self):
        if not hasattr(self, "image"):
            return
        
        print (self.path)

        try:
            idx = int(self.path.replace("/", "").split(".")[0])
        except:
            idx = None

        self.send_response(200)
        self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
        self.end_headers()
        im = None
        while True:
            # MAKE sure this refreshes the image every time
            if idx == None:
                im = self.image.copy()
            else:
                if idx >= len(self.pipe.chain_images[1]):
                    im = self.pipe.chain_images[0].copy()
                else:
                    im = self.pipe.chain_images[1][idx].copy()

            # encode image
            cv2s = cv2.imencode('.jpg', im)[1].tostring()

            # write a jpg
            self.wfile.write("--jpgboundary".encode())
            self.send_header('Content-type', 'image/jpeg')
            self.send_header('Content-length', str(len(cv2s)).encode())
            self.end_headers()
            self.wfile.write(cv2s)
            #self.wfile.write("<body>hello</body>".encode('utf-8'))
            while np.array_equal(self.image, im):
                time.sleep(0.01)

    def do_GET_HTML(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()

        if self.path.endswith("chain.html"):
            page = """
            <html>
                <head></head>
                <body>
            """

            for i in range(0, len(self.pipe.chain_images[1])):
                #my_name = inspect.getsourcelines(self.pipe.chain[i])[0][0]
                my_name = str(self.pipe.chain[i])
                page += """
                    <h2>{name}</h2>
                    <img src=\"/{num}.mjpg\"/><br />
                """.format(num=i, name=my_name)


            page += """
                
                </body>
            </html>
            """
            self.wfile.write(page.encode())
            
        else:
            self.wfile.write("""
            <html>
                <head></head>
                <body>
                <img src="whatever.mjpg"/>
                </body>
            </html>
            """.encode())

    def do_GET(self):
        #self.send_response(200)
        #self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
        #self.end_headers()

        if self.path.endswith('.html'):
            self.do_GET_HTML()
        elif self.path.endswith('.ico'):
            pass
        else:
            self.do_GET_MJPG()
            

class MJPGServer(VPL):
    """

    Usage: MJPGServer(port=5802, fps_cap=None)

      * "port" = the port to host it on

    This is code to host a web server

    This only works on google chrome, connect to "localhost:PORT" to see the image. Or, if you are hosting it on another device (such as a raspi), connect like (raspberrypi.local:PORT) in your browser

    """

    def process(self, pipe, image, data):
        if not hasattr(self, "http_server"):
            self.http_server = ThreadedHTTPServer(('0.0.0.0', self["port"]), MJPGStreamHandle)
            self.http_server.daemon_threads = True
            self.do_async(self.http_server.serve_forever)

        self.http_server.update_pipe(pipe)
        self.http_server.update_image(image.copy())

        return image, data

