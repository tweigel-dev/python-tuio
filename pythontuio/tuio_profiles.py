
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

from pythonosc.osc_message_builder import OscMessageBuilder
from pythonosc.osc_message import OscMessage
TUIO_CURSOR = "/tuio/2Dcur"
TUIO_OBJECT = "/tuio/2Dobj"
TUIO_BLOB   = "/tuio/2Dblb"

class Profile:
    """
    custom class of all subjects passing the TUIO connection.
    See more at https://www.tuio.org/?specification

    """

    def __init__(self, session_id):
        self.session_id = session_id

class Object(Profile):
    """
    TUIO Object 2D Interactive Surface
    """
    def __init__(self, session_id):
        super(Object, self).__init__(session_id)
        self.class_id               = -1            # i
        self.position               = (0, 0)   # x,y
        self.angle                  = 0             # a
        self.velocity               = (0, 0)   # X,Y
        self.velocity_rotation      = 0             # A
        self.motion_acceleration    = 0             # m
        self.rotation_acceleration  = 0             # r

    def get_message(self) -> OscMessage:
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
        self.position               = (0, 0)   # x,y
        self.velocity               = (0, 0)   # X,Y
        self.motion_acceleration    = 0             # m

    def get_message(self)-> OscMessage:
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
     # pylint: disable=too-many-instance-attributes
    """
    TUIO Blob 2D Interactive Surface
    """
    def __init__(self, session_id):
        super(Blob, self).__init__(session_id)
        self.position               = (0, 0)        # x,y
        self.angle                  =  5            # a
        self.dimension              = (.1, .1)      # w, h
        self.area                   = 0.1           # f
        self.velocity               = (0.1, 0.1)    # X,Y
        self.velocity_rotation      = 0.1           # A
        self.motion_acceleration    = 0.1           # m
        self.rotation_acceleration  = 0.1           # r

    def get_message(self)-> OscMessage:
        """
        returns the OSC message of the Blob with the TUIO spezification
        """
        x, y = self.position
        X, Y = self.velocity
        w, h = self.dimension
        builder = OscMessageBuilder(address=TUIO_BLOB)
        for val in [
                "set",
                self.session_id,
                float(x),
                float(y),
                float(self.angle),
                float(w),
                float(h),
                float(self.area),
                float(X),
                float(Y),
                float(self.velocity_rotation),
                float(self.motion_acceleration),
                float(self.rotation_acceleration)
        ]:
            builder.add_arg(val)
        return builder.build()
