
"""
              TuioDispatcher
                    |
                    |
            ---------------------
            |                   |
        TuioClient          TuioServer


"""


import threading
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
        self._fseq = 0
        self._fseq_lock = threading.Lock()

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

    @staticmethod
    def _build_fseq(address, frame_sequence):
        """Build a TUIO fseq message for one profile."""
        builder = OscMessageBuilder(address=address)
        builder.add_arg("fseq")
        builder.add_arg(frame_sequence)
        return builder.build()

    def next_fseq(self):
        """Allocate the next nonnegative OSC int32 frame sequence ID."""
        with self._fseq_lock:
            frame_sequence = self._fseq
            self._fseq = (self._fseq + 1) % (2**31)
            return frame_sequence

    def _build_profile_bundle(self, address, active_profiles, set_profiles, frame_sequence):
        """Build one ordered TUIO 1.1 profile-specific bundle."""
        bundle_builder = OscBundleBuilder(0)
        bundle_builder.add_content(TuioServer._build_alive(address, active_profiles))
        for profile in set_profiles:
            bundle_builder.add_content(profile.get_message())
        bundle_builder.add_content(TuioServer._build_fseq(address, frame_sequence))
        return bundle_builder.build()

    def _send_profile_bundle(self, address, active_profiles, set_profiles, frame_sequence):
        bundle = self._build_profile_bundle(
            address,
            list(active_profiles),
            list(set_profiles),
            frame_sequence,
        )
        self.send(bundle)

    def send_bundle(self):
        """Send the current state as TUIO 1.1 profile-specific bundles."""
        frame_sequence = self.next_fseq()

        cursors = list(self.cursors)
        self._send_profile_bundle(TUIO_CURSOR, cursors, cursors, frame_sequence)

        objects = list(self.objects)
        self._send_profile_bundle(TUIO_OBJECT, objects, objects, frame_sequence)

        blobs = list(self.blobs)
        self._send_profile_bundle(TUIO_BLOB, blobs, blobs, frame_sequence)

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
