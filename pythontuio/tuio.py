
"""
TUIO client and server classes based on python-osc.

              TuioDispatcher
                    |
                    |
            ---------------------
            |                   |
        TuioClient          TuioServer


"""


import socket
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
    In order to receive and decode TUIO messages, an instance of TuioClient needs to be created.
    The TuioClient instance then generates TUIO events which are broadcast to all
    registered listeners that implement the TuioListener interface.
    """
    def __init__(self, server_address: Tuple[str, int]): # pylint: disable=W0231
        TuioDispatcher.__init__(self)
        self._dispatcher = self
        self.connected = False
        self.server_address = server_address
        self._lifecycle_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._serve_done = threading.Event()
        self._thread = None
        self._serving_ident = None

    def start(self, blocking=True):
        """
        Start receiving UDP OSC packets.

        With the default blocking=True the method blocks in the current thread
        until stop() is called from another thread, preserving the historic
        behavior. With blocking=False the receive loop runs in an internal
        non-daemon thread and the method returns immediately; stop() must be
        called before the application exits.
        """
        with self._lifecycle_lock:
            if self.connected:
                raise RuntimeError("TuioClient is already running")
            print(f"starting tuio-client at port {self.server_address[1]}")
            BlockingOSCUDPServer.__init__(self,self.server_address, self)
            self._stop_event.clear()
            self._serve_done.clear()
            self.connected = True
            if not blocking:
                self._thread = threading.Thread(
                    target=self._serve,
                    name="tuio-client-receiver",
                    daemon=False,
                )
                try:
                    self._thread.start()
                except Exception:
                    self._thread = None
                    self.connected = False
                    self.server_close()
                    raise
        if blocking:
            self._serve()

    def stop(self):
        """
        Stop receiving UDP OSC packets and clear all decoded TUIO state.

        Active cursors, objects and blobs are removed silently without remove
        callbacks, following the reference client disconnect behavior. Does
        nothing if the client is not running. Must not be called from the
        receiver thread, e.g. from inside a listener callback.
        """
        if self._serving_ident is not None and self._serving_ident == threading.get_ident():
            raise RuntimeError("stop() must not be called from the client receiver thread")
        with self._lifecycle_lock:
            if not self.connected:
                return
            self._stop_event.set()
        self._wake_receiver()
        while not self._serve_done.wait(0.5):
            self._wake_receiver()
        thread = self._thread
        if thread is not None:
            thread.join()
            self._thread = None
        with self._lifecycle_lock:
            self.connected = False
            self._reset_state()

    def _serve(self):
        """Receive loop running in the current or internal receiver thread."""
        self._serving_ident = threading.get_ident()
        try:
            while not self._stop_event.is_set():
                self.handle_request()
        finally:
            self._serving_ident = None
            self.server_close()
            self._serve_done.set()

    def _wake_receiver(self):
        """Send a dummy byte to the client's own socket to unblock the receive loop."""
        try:
            host, port = self.socket.getsockname()[:2]
        except OSError:
            return
        if host in ("", "0.0.0.0"):
            host = "127.0.0.1"
        elif host == "::":
            host = "::1"
        try:
            wake_socket = socket.socket(self.address_family, socket.SOCK_DGRAM)
            try:
                wake_socket.sendto(b"\x00", (host, port))
            finally:
                wake_socket.close()
        except OSError:
            pass

class TuioServer(TuioDispatcher, UDPClient):

    """
    A TUIO server based on the UDP client implementation of python-osc.
    """

    def __init__(self, ip: str ="127.0.0.1" , port :int=3333):
        UDPClient.__init__(self,ip, port)
        TuioDispatcher.__init__(self)
        self.is_full_update : bool = False
        self._periodic_messages : bool = False
        self._source_name = ""
        self._fseq = 0
        self._fseq_lock = threading.Lock()
        self._enabled_profiles = {TUIO_CURSOR, TUIO_OBJECT, TUIO_BLOB}
        self._periodic_lock = threading.Lock()
        self._periodic_thread = None
        self._periodic_stop = None

    @staticmethod
    def _build_alive(address, profile_list):
        """
        Build and return an OSC alive message for one TUIO profile.
        """
        builder = OscMessageBuilder(address=address)
        builder.add_arg("alive")
        for profile in profile_list:
            builder.add_arg(profile.session_id) # add session IDs of active profiles

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

    def _enabled_profiles_state(self):
        """Return enabled profiles as (address, profile list, enabled) tuples."""
        return (
            (TUIO_CURSOR, self.cursors, self.has_cursor_profile()),
            (TUIO_OBJECT, self.objects, self.has_object_profile()),
            (TUIO_BLOB, self.blobs, self.has_blob_profile()),
        )

    def _send_current_state(self, frame_sequence):
        for address, profile_list, enabled in self._enabled_profiles_state():
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
        """Return True if the cursor profile is enabled."""
        return TUIO_CURSOR in self._enabled_profiles

    def has_object_profile(self):
        """Return True if the object profile is enabled."""
        return TUIO_OBJECT in self._enabled_profiles

    def has_blob_profile(self):
        """Return True if the blob profile is enabled."""
        return TUIO_BLOB in self._enabled_profiles

    def disable_periodic_messages(self):
        """Disable the periodic retransmission of TUIO state.

        Stops the internal timer thread if it is running. Does nothing if
        periodic messages are not enabled.
        """
        with self._periodic_lock:
            self._stop_periodic_thread()

    def _stop_periodic_thread(self):
        """Stop the periodic timer thread. Caller must hold _periodic_lock."""
        self._periodic_messages = False
        thread = self._periodic_thread
        stop_event = self._periodic_stop
        self._periodic_thread = None
        self._periodic_stop = None
        if thread is not None:
            stop_event.set()
            thread.join()

    def enable_periodic_messages(self, intervall: int = 1000):
        """Enable periodic retransmission of TUIO state.

        Every intervall milliseconds the current state is resent with the
        redundant frame marker fseq -1, so clients joining a static scene or
        recovering from packet loss can resynchronize. If the public
        is_full_update attribute is true the complete state including all set
        messages is transmitted, otherwise only alive keepalive bundles are
        sent. Retransmission runs in a daemon thread and therefore does not
        keep the application alive.
        """
        if intervall <= 0:
            raise ValueError("intervall must be a positive number of milliseconds")
        with self._periodic_lock:
            self._stop_periodic_thread()
            self._periodic_messages = True
            self._periodic_stop = threading.Event()
            self._periodic_thread = threading.Thread(
                target=self._periodic_loop,
                args=(self._periodic_stop, intervall),
                name="tuio-server-periodic",
                daemon=True,
            )
            self._periodic_thread.start()

    def periodic_messages_enabled(self):
        """Return True if periodic retransmission is enabled."""
        return self._periodic_messages

    def _periodic_loop(self, stop_event, intervall):
        """Timer loop sending redundant state until stopped."""
        while not stop_event.wait(intervall / 1000.0):
            self._send_periodic_state()

    def _send_periodic_state(self):
        """Send one redundant resynchronization or keepalive frame."""
        if self.is_full_update:
            self.send_full_messages()
            return
        for address, profile_list, enabled in self._enabled_profiles_state():
            if enabled:
                self.send_profile_bundle(address, list(profile_list), [], fseq=-1)

    def set_source_name(self, _name : str, ip :str=None):
        """Set the optional TUIO source name sent at the start of each bundle."""
        if ip is None:
            self._source_name = str(_name)
        else:
            self._source_name = f"{_name}@{ip}"
