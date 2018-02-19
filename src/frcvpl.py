"""

Copyright 2017 LN STEMpunks & ChemicalDevelopment

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


from enum import Enum
import enum
import time
import threading
import math
import os
import glob
import pathlib

from http.server import BaseHTTPRequestHandler,HTTPServer
from socketserver import ThreadingMixIn

from networktables import NetworkTables
import wpilib
import re
import cv2
import vpl.all

import numpy as np



"""

definition of all opencv cap props

"""

"""

frcvpl = video pipe line

Think of it similar to how VSTs handle audio, this is a plugin for video

"""

import cv2



class InRange(vpl.VPL):
    """

    Usage: InRange(H=(20, 40), S=(30, 60), V=(100, 200), mask_key=None)

    """
    def process(self, pipe, image, data):
        H = self.get("H", (23, 37))
        S = self.get("S", (79, 255))
        V = self.get("V", (103, 255))
        mask = cv2.inRange(image, (H[0],S[0],V[0]), (H[1],S[1],V[1]))
        mask_key = self.get("mask_key", None)
        if mask_key is not None:
            data[mask_key] = mask

        return image, data

class ApplyMask(vpl.VPL):
    """

    Usage: ApplyMask(mask_key=None)

    """
    def process(self, pipe, image, data):
        mask_key = self.get("mask_key", None)
        if mask_key is not None:
            res = cv2.bitwise_and(image, image, mask=data[mask_key])
            return res, data
        else:
            return image, data

class FindContours(vpl.VPL):
    """ 

    Usage: FindCountours(key="contours")

    """
    def process(self, pipe, image, data):
        # find contours in the mask and initialize the current
        
        cnts = cv2.findContours(image, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[-2]
        center = None

        data[self["key"]] = []

        # only proceed if at least one contour was found
        if len(cnts) > 0:
            # find the largest contour in the mask, then use
            # it to compute the minimum enclosing circle and
            # centroid
            c = max(cnts, key=cv2.contourArea)
            ct = 0
            #for c in filter(lambda x: cv2.contourArea(x) > 15, cnts):
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
            # only proceed if the radius meets a minimum size
            if (radius > 10):
                data[self["key"]] += [[center, radius]]
                """
                # draw the circle and centroid on the frame,
                # then update the list of tracked points
                cv2.rectangle(image ,(int(x)-int(radius), int(y)+int(radius)),(int(x)+int(radius), int(y)-int(radius)),(0,255,0),3)
                cv2.putText(image,'LargestContour ' + str(round(x,1)) + ' ' + str(round(y,1)),(int(x)-int(radius), int(y)-int(radius)), cv2.FONT_HERSHEY_PLAIN, 2*(int(radius)/45),(255,255,255),2,cv2.LINE_AA)

                #cv.rectangle(frame , ((int(x)- int(radius), (int(y)+int(radius)) , (1,1),(0,255,0),3)
                cv2.circle(image, center, 5, (255 * (ct % 3 == 2), 255 * (ct % 3 == 1), 255 * (ct % 3 == 0)), -1)
                """
            ct += 1
        return image, data

class DrawContours(vpl.VPL):

    def process(self, pipe, image, data):
        contours = data[self["key"]]
        for center, radius in contours:
            cv2.circle(image, center, 5, (255, 0, 0), -1)
        return image, data

class StoreImage(vpl.VPL): 
    
    def process(self, pipe, image, data):
        key = self.get("key", None)
        if key is not None:
            data[key] = image.copy()
        return image, data

class RestoreImage(vpl.VPL): 
    
    def process(self, pipe, image, data):
        key = self.get("key", None)
        if key is not None:
            image = data[key]
        return image, data



class Distance(vpl.VPL):
    """

    Calculates Distance to Radius
    A: 17in
    B: 109in
    C: 109.32977636490435

    5150/x

    """
    def process(self, pipe, image, data):
        contours = data[self["key"]]
        if len(contours) != 0:
            contours = data[self["key"]]
            for center, radius in contours:
               distance = 5150/radius if radius != 0 else 0
               cv2.putText(image, str(distance), (100,100), cv2.FONT_HERSHEY_PLAIN, 2,  (0,255,255))

        return image, data

class KillSwitch(vpl.VPL):
    def process(self, pipe, image, data):
        c = cv2.waitKey(7) % 0x100
        if c in (10, 27, 113):
            pipe.quit()
        return image, data
    


class DrawMeter(vpl.VPL):
    '''

    Draws a rectangle in the lower left hand corner and scales the x values of the center point. Similar to our previous implementation of light on the robot. 

    '''

    def process(self, pipe, image, data):
        contours = data[self["key"]]
        h,w,bpp = np.shape(image)
        bar_width = 290
        range_lower = int((w/2)-50)
        range_upper = int((w/2)+50)


        for center, radius in contours:
            x = center[0]
            if x > range_lower and x < range_upper:
                bar_color = (34,139,34)
            else:
                bar_color = (0,0,255)
                

            cv2.rectangle(image, (w-10,h-10), (w-300,h-50) , (0,255,255), cv2.FILLED)
            cv2.rectangle(image,((int(((x/w)*bar_width)+330)),h-5), ((int(((x/w)*bar_width)+350)),h-55), bar_color, cv2.FILLED)

        return image, data


class ShowGameInfo(vpl.VPL):

    def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.firstScroll = 0
            self.secondScroll = -400

    
    def process(self, pipe, image, data):

        def drawInfo(image):

            height, width, channels = image.shape

            if self.firstScroll < width:
                self.firstScroll = self.firstScroll + 1
            else: 
                self.firstScroll = -(width+1000)
            if self.secondScroll < width:
                self.secondScroll = self.secondScroll + 1
            elif self.firstScroll == width/2:
                self.secondScroll = int((width/2.5)*-1)

            #draw rectangle
            cv2.rectangle(image, (0, height), (width,int(height-(height*.06))), (244,244,244), cv2.FILLED, lineType=8, shift=0)

            font = cv2.FONT_HERSHEY_SIMPLEX

            alliance = wpilib.DriverStation.getInstance().getAlliance()
            eventName = eventName = wpilib.DriverStation.getInstance().getEventName()
            matchTime = matchTime = wpilib.DriverStation.getInstance().getMatchTime()
            autonomous = autonomous = wpilib.DriverStation.getInstance().isAutonomous()
            systemAttached = systemAttached = wpilib.DriverStation.getInstance().isFMSAttached()

            infoText = "Alliance: " + (str(alliance) + "Event Name: " +  str(eventName) + "Match Time: " + str(matchTime) + "Autonomous: " + str(autonomous) + "System Attached: " + str(systemAttached))

            cv2.putText(image, infoText, (self.firstScroll,int(height-(height*.01))), font, 1, (0,0,255),2) 
            cv2.putText(image, "L&N STEMpunks", (self.secondScroll,int(height-(height*.01))), font, 1, (0,0,255),2) 
            auto = True
          #  if auto == True:
                #cv2.putText(image, "Autonomous Period", ((0, -(height/6) ), ((width/5),-(height/5))), font, 1, (0,0,255),2) 

        drawInfo(image)

        return image, data

class DumpInfo(vpl.VPL):

    def write(self):
        if len(self.contours) != 0:
            for center, radius in self.contours:
                x,y = center
                print(center, radius)

                self.smartdashboard.putNumber("Radius", radius)
                self.smartdashboard.putNumber("centerX", x)
                self.smartdashboard.putNumber("centerY", y)
        else:
            self.smartdashboard.putNumber("Radius", -1)
            self.smartdashboard.putNumber("centerX", -1)
            self.smartdashboard.putNumber("centerY", -1)


    def process(self, pipe, image, data):
        self.contours = data[self["key"]]
        if not hasattr(self, "is_init"):
            self.is_init = True

            NetworkTables.initialize(server='roborio-3966-FRC.local')
            self.smartdashboard = NetworkTables.getTable('SmartDashboard')

        if not hasattr(self, "last_time") or time.time() - self.last_time > 1.0 / 24.0:
            self.write()
            self.last_time = time.time()
        return image, data