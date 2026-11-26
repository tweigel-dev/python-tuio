
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
    TUIO server based on the UDP client implementation of python-osc.
    """

    def __init__(self, ip: str ="127.0.0.1" , port :int=3333):
        UDPClient.__init__(self,ip, port)
        TuioDispatcher.__init__(self)
        self.is_full_update : bool = False
        self._periodic_messages : bool = False
        self._intervall : int = 1000
        self._source_name = ""
        self._fseq = 0
        self._fseq_lock = threading.Lock()
        self._enabled_profiles = {TUIO_CURSOR, TUIO_OBJECT, TUIO_BLOB}

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
    def _build_source(address, source_name):
        """Build a TUIO source message for one profile."""
        builder = OscMessageBuilder(address=address)
        builder.add_arg("source")
        builder.add_arg(source_name)
        return builder.build()

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
        if self._source_name:
            bundle_builder.add_content(TuioServer._build_source(address, self._source_name))
        bundle_builder.add_content(TuioServer._build_alive(address, active_profiles))
        for profile in set_profiles:
            bundle_builder.add_content(profile.get_message())
        bundle_builder.add_content(TuioServer._build_fseq(address, frame_sequence))
        return bundle_builder.build()

    def send_profile_bundle(self, address, active_profiles, set_profiles=None, fseq=None):
        """Send one TUIO profile bundle.

        active_profiles determines the complete alive list, while set_profiles
        determines which set messages are included. If fseq is omitted, the
        next frame sequence ID is allocated automatically.
        """
        active_profiles = list(active_profiles)
        if set_profiles is None:
            set_profiles = active_profiles
        else:
            set_profiles = list(set_profiles)
        if fseq is None:
            fseq = self.next_fseq()

        bundle = self._build_profile_bundle(address, active_profiles, set_profiles, fseq)
        self.send(bundle)
        return fseq

    def _send_current_state(self, frame_sequence):
        profiles = (
            (TUIO_CURSOR, self.cursors, self.has_cursor_profile()),
            (TUIO_OBJECT, self.objects, self.has_object_profile()),
            (TUIO_BLOB, self.blobs, self.has_blob_profile()),
        )
        for address, profile_list, enabled in profiles:
            if enabled:
                active_profiles = list(profile_list)
                self.send_profile_bundle(
                    address,
                    active_profiles,
                    active_profiles,
                    fseq=frame_sequence,
                )

    def send_bundle(self):
        """Send the current state as TUIO 1.1 profile-specific bundles."""
        self._send_current_state(self.next_fseq())

    def send_full_messages(self):
        """Send redundant full state for all enabled profiles with fseq -1."""
        self._send_current_state(-1)

    def send_empty_cursor_bundle(self):
        """Send an empty cursor bundle for startup or shutdown state clearing."""
        self.send_profile_bundle(TUIO_CURSOR, [], [], fseq=-1)

    def send_empty_object_bundle(self):
        """Send an empty object bundle for startup or shutdown state clearing."""
        self.send_profile_bundle(TUIO_OBJECT, [], [], fseq=-1)

    def send_empty_blob_bundle(self):
        """Send an empty blob bundle for startup or shutdown state clearing."""
        self.send_profile_bundle(TUIO_BLOB, [], [], fseq=-1)

    def _set_profile_enabled(self, address, flag):
        if flag:
            self._enabled_profiles.add(address)
        else:
            self._enabled_profiles.discard(address)

    def enable_cursor_profile(self, flag=True):
        """Enable or disable the /tuio/2Dcur cursor profile."""
        self._set_profile_enabled(TUIO_CURSOR, flag)

    def enable_object_profile(self, flag=True):
        """Enable or disable the /tuio/2Dobj object profile."""
        self._set_profile_enabled(TUIO_OBJECT, flag)

    def enable_blob_profile(self, flag=True):
        """Enable or disable the /tuio/2Dblb blob profile."""
        self._set_profile_enabled(TUIO_BLOB, flag)

    def has_cursor_profile(self):
        """Return true if the cursor profile is enabled."""
        return TUIO_CURSOR in self._enabled_profiles

    def has_object_profile(self):
        """Return true if the object profile is enabled."""
        return TUIO_OBJECT in self._enabled_profiles

    def has_blob_profile(self):
        """Return true if the blob profile is enabled."""
        return TUIO_BLOB in self._enabled_profiles

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
        """Set the optional TUIO source name sent at the start of each bundle."""
        if ip is None:
            self._source_name = str(_name)
        else:
            self._source_name = f"{_name}@{ip}"
