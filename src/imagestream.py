import threading

import time
import sys
import os
import argparse

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SocketServer import ThreadingMixIn

import cv2

imgdraw = None

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	"""Handle requests in a separate thread."""


class StreamHandle(BaseHTTPRequestHandler):		

	def do_GET(self):
		global imgdraw	
		self.send_response(200)
		self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
		self.end_headers()
		while True:
			try:
				im = cv2.cvtColor(imgdraw.getImage(), cv2.COLOR_HLS2BGR)
				cv2s = cv2.imencode('.jpg', im)[1].tostring()

				self.wfile.write("--jpgboundary")
				self.send_header('Content-type','image/jpeg')
				self.send_header('Content-length', str(len(cv2s)))
				self.end_headers()
				self.wfile.write(cv2s)
				time.sleep(1.0 / imgdraw.args.fps)
			except KeyboardInterrupt:
				break
		return

