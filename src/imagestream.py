
import time
import sys
import os
import argparse

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SocketServer import ThreadingMixIn

import cv2

pipe = None

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	"""Handle requests in a separate thread."""


class StreamHandle(BaseHTTPRequestHandler):		

	def do_GET(self):
		global pipe
		self.send_response(200)
		self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
		self.end_headers()
		while True:
			# MAKE sure this refreshes the image every time
			try:
				cv2s = cv2.imencode('.jpg', pipe.im["output"])[1].tostring()

				self.wfile.write("--jpgboundary")
				self.send_header('Content-type','image/jpeg')
				self.send_header('Content-length', str(len(cv2s)))
				self.end_headers()
				self.wfile.write(cv2s)
				time.sleep(1.0 / pipe.args.fps)
			except KeyboardInterrupt:
				break
		return

