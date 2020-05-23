import argparse
import random
import time
from datetime import datetime

from collections import Iterable
from pythonosc import udp_client
from pythonosc.osc_message_builder import OscMessageBuilder
from pythonosc.osc_bundle_builder import OscBundleBuilder
from pythonosc.osc_message import OscMessage
from pythonosc.osc_bundle import OscBundle
from typing import Union
"""
this python file is written orientated by the TUIO spezification 
https://www.tuio.org/?specification
It supports only 2D Object|Blob|Cursor

            Profile
                |
    ---------------------
    |           |       |
  Object     Cursor    Blob


"""

TUIO_CURSOR = "/tuio/2Dcur"


class TuioClient(udp_client.UDPClient):

    def __init__(self, ip="127.0.0.1", port=3333 ):
        super(TuioClient, self).__init__(ip, port)

        self.cursors = []
        self.objects = []
        self.blobs   = []

    def send_bundle(self ):
        """Build :class:`OscMessage` from arguments and send to server

        Args:
            address: OSC address the message shall go to
            value: One or more arguments to be added to the message
        """

        bundle_builder = OscBundleBuilder(0)

        # build alive message

        builder = OscMessageBuilder(address=TUIO_CURSOR)

        builder.add_arg("alive")
        for cursor  in self.cursors:
            builder.add_arg(cursor.session_id) ## add id 
        alive_msg = builder.build()
        bundle_builder.add_content(alive_msg)

        # set message of cursor
        
        for cursor in self.cursors:
            cursor_msg = cursor._get_message()
            bundle_builder.add_content(cursor_msg)

        # set message of blob
        # for blob in self.blobs:
        #     blob_msg = blob._get_message()
        #     bundle_builder.add_content(blob_msg)

        # # set message of object
        # for o in self.objects:
        #     object_msg = o._get_message()
        #     bundle_builder.add_content(object_msg)

        # message fseq to end the bundle and send (optinal) frame id 
        builder = OscMessageBuilder(address=TUIO_CURSOR)
        builder.add_arg("fseq")
        builder.add_arg(-1)
        fseq = builder.build()
        bundle_builder.add_content(fseq)

        # build bundle and send
        bundle = bundle_builder.build()
        self.send(bundle)




class Profile:
    """
    custom class of all subjects passing the TUIO connection. See more at https://www.tuio.org/?specification

    """

    def __init__(self, session_id= None):
        self.session_id = session_id

class Object(Profile):
    def __init__(self):  
        self.position=tuple()          # x,y  
        self.angle                     # a  
        self.velocity = tuple()        # X,Y
        self.velocity_rotation         # A
        self.motion_acceleration       # m
        self.rotation_acceleration     # r


    def send_update(self):
        self.client.send_message("/tuio/2Dobj", str.encode(self._get_message()))

    def _get_message(self):
        x, y = self.position
        X, Y = self.velocity
        return f"set {self.session_id} {self.class_id} {x} {y} {self.angle} {X} {Y} {self.velocity_rotation} {self.motion_acceleration} {self.rotation_acceleration} " 

class Cursor(Profile):
    def __init__(self):
        super(Cursor, self).__init__()
        self.position               = tuple()       # x,y
        self.velocity               = tuple()       # X,Y
        self.motion_acceleration    = 0             # m

    # def send_update(self):
    #     message = self._get_message()

    #     #print(f"/tuio/2Dcur {message}")
    #     self.client.send_message(f"/tuio/2Dcur", message)
        
    def _get_message(self):
        x, y = self.position
        X, Y = self.velocity
        builder = OscMessageBuilder(address=TUIO_CURSOR)
        for val in ["set", self.session_id, float(x), float(y), float(X), float(Y), float(self.motion_acceleration)]:
            builder.add_arg(val)
        return builder.build()


class Blob(Profile):

    def __init__(self):
        self.client = Client()
        self.position = tuple()        # x,y
        self.angle   =  0            # a dosen`t understand this value
        self.dimension =(1,1)        # w, h
        self.area                    # f
        self.velocity = tuple()      # X,Y
        self.velocity_rotation       # A
        self.motion_acceleration     # m
        self.rotation_acceleration   # r

    def send_update(self):
        self.client.send_message("/tuio/2Dblb",  str.encode(self._get_message()))

    def _get_message(self):
        x, y = self.position
        X, Y = self.velocity
        return f"set {self.session_id} {x} {y} {self.angle} {self.dimension} {self.area} {X} {Y} {velocity_rotation} {self.motion_acceleration} {self.rotation_acceleration}"


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--ip", default="127.0.0.1",
    #     help="The ip of the OSC server")
    # parser.add_argument("--port", type=int, default=5005,
    #     help="The port the OSC server is listening on")
    # args = parser.parse_args()

    client = TuioClient()

    i = 0
    cursor = Cursor()

    cursor.velocity             = (0.2,0.1)
    cursor.motion_acceleration  = 0.1 
    cursor.session_id    = 123

    client.cursors.append(cursor)
    while i < 10:

    
        i+=1
        cursor.position             = (0.5+0.01*i,0.5)

        client.send_bundle()
        print("sented message")
        time.sleep(0.1)

