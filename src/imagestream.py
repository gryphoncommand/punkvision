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



import time
import sys
import os
import argparse

from http.server import BaseHTTPRequestHandler,HTTPServer
from socketserver import ThreadingMixIn

import cv2


holder = None
fps = 24.0

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


class StreamHandle(BaseHTTPRequestHandler):        

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
        self.end_headers()
        global holder
        global fps
        while True:
            # MAKE sure this refreshes the image every time
            try:
                cv2s = cv2.imencode('.jpg', holder.im["output"])[1].tostring()

                self.wfile.write("--jpgboundary".encode())
                self.send_header('Content-type','image/jpeg')
                self.send_header('Content-length', str(len(cv2s)).encode())
                self.end_headers()
                self.wfile.write(cv2s)
                time.sleep(1.0 / fps)
            except KeyboardInterrupt:
                break
        return

