
"""
              TuioDispatcher
                    |
                    |
            ---------------------
            |                   |
        TuioClient          TuioServer


"""


from typing import  Tuple


from pythonosc.udp_client import UDPClient
from pythonosc.osc_server import BlockingOSCUDPServer

from pythonosc.osc_message_builder import OscMessageBuilder
from pythonosc.osc_bundle_builder import OscBundleBuilder
from pythontuio.const import TUIO_BLOB, TUIO_CURSOR, TUIO_OBJECT
from pythontuio.dispatcher import TuioDispatcher



class TuioClient(TuioDispatcher, BlockingOSCUDPServer): # pylint: disable=too-many-ancestors
    """
    The TuioClient class is the central TUIO protocol decoder component.
    It provides a simple callback infrastructure using the TuioListener interface.
    In order to receive and decode TUIO messages an instance of TuioClient needs to be created.
    The TuioClient instance then generates TUIO events which are broadcasted to all
    registered classes that implement the TuioListener interface.
    """
    def __init__(self, server_address: Tuple[str, int]): # pylint: disable=W0231
        TuioDispatcher.__init__(self)
        self._dispatcher = self
        self.connected = False
        self.server_address = server_address
    def start(self):
        """
        start serving for UDP OSC packages
        """
        print(f"starting tuio-client at port {self.server_address[1]}")
        BlockingOSCUDPServer.__init__(self,self.server_address, self)
        self.serve_forever()

class TuioServer(TuioDispatcher, UDPClient):

    """
    Tuio client based on a basic osc udp client of the lib python-osc

    Notice that TuioSource is not implemented yet
    """

    def __init__(self, ip: str ="127.0.0.1" , port :int=3333):
        UDPClient.__init__(self,ip, port)
        TuioDispatcher.__init__(self)
        self._ip = ip
        self._port = port

        self.is_full_update : bool = False
        self._periodic_messages : bool = False
        self._intervall : int = 1000

    @staticmethod
    def _build_alive(address, profile_list):
        """
        builds a OSC which implements a alive message of TUIO
        returns the message
        """
        builder = OscMessageBuilder(address=address)
        builder.add_arg("alive")
        for profile in profile_list:
            builder.add_arg(profile.session_id) ## add id of cursors

        alive_msg = builder.build()
        return alive_msg
    def send_bundle(self):
        """Build :class:`OscMessage` from arguments and send to server

        Args:
            address: OSC address the message shall go to
            value: One or more arguments to be added to the message
        """

        bundle_builder = OscBundleBuilder(0)

        # build alive message
        if len(self.cursors) != 0:
            bundle_builder.add_content(TuioServer._build_alive(TUIO_CURSOR,self.cursors))
        if len(self.blobs) != 0:
            bundle_builder.add_content(TuioServer._build_alive(TUIO_BLOB,self.blobs))
        if len(self.objects) != 0:
            bundle_builder.add_content(TuioServer._build_alive(TUIO_OBJECT,self.objects))


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

    def disable_periodic_messages(self, ):
        """
        Not implemented
        """
        self._periodic_messages = False
        raise Exception("Not implemented")

    def enable_periodic_messages(self, intervall:int):
        """
        Not implemented
        """
        self._periodic_messages = True
        self._intervall = intervall
        raise Exception("Not implemented")

    def set_source_name(self, _name : str, ip :str=None):
        """
        Not implemented
        """
        if ip is not None:
            ip = self._ip

        raise Exception("Not implemented")
