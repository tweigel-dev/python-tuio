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

from pythonosc import udp_client
from pythonosc.osc_message_builder import OscMessageBuilder
from pythonosc.osc_bundle_builder import OscBundleBuilder



TUIO_CURSOR = "/tuio/2Dcur"
TUIO_OBJECT = "/tuio/2Dobj"
TUIO_BLOB   = "/tuio/2Dblb"

class TuioServer(udp_client.UDPClient):
    """
    Tuio client based on a basic osc udp client of the lib python-osc
    """
    def __init__(self, ip="127.0.0.1", port=3333):
        super(TuioServer, self).__init__(ip, port)

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
            builder.add_arg(cursor.session_id) ## add id of cursors
        alive_msg = builder.build()

        for cursor  in self.blobs:
            builder.add_arg(cursor.session_id) ## add id of blobs
        alive_msg = builder.build()

        for cursor  in self.objects:
            builder.add_arg(cursor.session_id) ## add id of objects
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


