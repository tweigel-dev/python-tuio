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

from collections import Iterable
from pythonosc import udp_client
from pythonosc.osc_message_builder import OscMessageBuilder
from pythonosc.osc_bundle_builder import OscBundleBuilder



TUIO_CURSOR = "/tuio/2Dcur"
TUIO_OBJECT = "/tuio/2Dobj"
TUIO_BLOB   = "/tuio/2Dblb"

class TuioClient(udp_client.UDPClient):

    def __init__(self, ip="127.0.0.1", port=3333):
        super(TuioClient, self).__init__(ip, port)

        self.cursors = []
        self.objects = []
        self.blobs   = []

    def send_bundle(self):
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
            cursor_msg = cursor.get_message()
            bundle_builder.add_content(cursor_msg)

        # set message of blob
        for blob in self.blobs:
            blob_msg = blob.get_message()
            bundle_builder.add_content(blob_msg)

        # set message of object
        for o in self.objects:
            object_msg = o.get_message()
            bundle_builder.add_content(object_msg)

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

    def __init__(self, session_id):
        self.session_id = session_id

class Object(Profile):
    """
    TUIO Object 2D Interactive Surface
    """
    def __init__(self, session_id):  
        super(Object, self).__init__(session_id)
        self.class_id               = -1        # i   
        self.position               = tuple()   # x,y  
        self.angle                  = 0         # a  
        self.velocity               = tuple()   # X,Y
        self.velocity_rotation      = 0         # A
        self.motion_acceleration    = 0         # m
        self.rotation_acceleration  = 0         # r

    def get_message(self):
        """
        returns the OSC message of the Object with the TUIO spezification
        """
        x, y = self.position
        X, Y = self.velocity
        builder = OscMessageBuilder(address=TUIO_OBJECT)
        for val in [
                "set",
                int(self.session_id),
                int(self.class_id),
                float(x),
                float(y),
                float(self.angle),
                float(X),
                float(Y),
                float(self.velocity_rotation),
                float(self.motion_acceleration),
                float(self.rotation_acceleration)
        ]:
            builder.add_arg(val)
        return builder.build()

class Cursor(Profile):
    """
    TUIO Cursor 2D Interactive Surface
    """
    def __init__(self, session_id):
        super(Cursor, self).__init__(session_id)
        self.position               = tuple()       # x,y
        self.velocity               = tuple()       # X,Y
        self.motion_acceleration    = 0             # m
  
    def get_message(self):
        """
        returns the OSC message of the Cursor with the TUIO spezification
        """
        x, y = self.position
        X, Y = self.velocity
        builder = OscMessageBuilder(address=TUIO_CURSOR)
        for val in [
                "set",
                self.session_id,
                float(x),
                float(y),
                float(X),
                float(Y),
                float(self.motion_acceleration)
        ]:
            builder.add_arg(val)
        return builder.build()


class Blob(Profile):
    """
    TUIO Blob 2D Interactive Surface
    """
    def __init__(self, session_id):
        super(Blob, self).__init__(session_id)
        self.position               = tuple()   # x,y
        self.angle                  =  0        # a 
        self.dimension              =(.1,.1)    # w, h
        self.area                   = None      # f
        self.velocity               = tuple()   # X,Y
        self.velocity_rotation      = 0         # A
        self.motion_acceleration    = 0         # m
        self.rotation_acceleration  = 0         # r

    def get_message(self):
        """
        returns the OSC message of the Blob with the TUIO spezification
        """
        x, y = self.position
        X, Y = self.velocity
        builder = OscMessageBuilder(address=TUIO_BLOB)
        for val in [
                "set",
                self.session_id,
                float(x),
                float(y),
                float(self.angle),
                float(self.dimension),
                float(self.area),
                float(X),
                float(Y),
                float(self.velocity_rotation),
                float(self.motion_acceleration),
                float(self.rotation_acceleration)
        ]:
            builder.add_arg(val)
        return builder.build()
