"""
classes to handle incoming osc messages
"""
from abc import ABC # abstract base class of python
from collections import OrderedDict
from typing import List
from pythonosc.dispatcher import Dispatcher

from pythontuio.tuio_profiles import Cursor, Blob, Object
from pythontuio.tuio_profiles import TUIO_BLOB, TUIO_CURSOR, TUIO_OBJECT

from pythontuio.const import TUIO_END,TUIO_ALIVE,TUIO_SET, TUIO_SOURCE


_NO_ALIVE = object()
_PROFILE_ORDER = (TUIO_CURSOR, TUIO_OBJECT, TUIO_BLOB)
_SET_LENGTHS = {
    TUIO_CURSOR: 6,
    TUIO_OBJECT: 10,
    TUIO_BLOB: 12,
}


# pylint: disable=unnecessary-pass
class TuioListener(ABC):
    """
    Abstract TuioListener to define callbacks für the diffrent tuio events
    """
    def add_tuio_object(self, obj):
        """Abstract function to add a behavior for tuio add object event"""
        pass
    def update_tuio_object(self, obj):
        """Abstract function to add a behavior for tuio update object event"""
        pass
    def remove_tuio_object(self, obj):
        """Abstract function to add a behavior for tuio remove object event"""
        pass

    def add_tuio_cursor(self, cur):
        """Abstract function to add a behavior for tuio add cursor event"""
        pass
    def update_tuio_cursor(self, cur):
        """Abstract function to add a behavior for tuio update cursor event"""
        pass
    def remove_tuio_cursor(self, cur):
        """Abstract function to add a behavior for tuio remove cursor event"""
        pass

    def add_tuio_blob(self, blob):
        """Abstract function to add a behavior for tuio add blob event"""
        pass
    def update_tuio_blob(self, blob):
        """Abstract function to add a behavior for tuio update blob event"""
        pass
    def remove_tuio_blob(self, blob):
        """Abstract function to add a behavior for tuio remove blob event"""
        pass
    def refresh(self, time):
        """Abstract This callback method is invoked by the TuioClient
        to mark the end of a received TUIO message bundle."""
        pass
# pylint: enable=unnecessary-pass


class TuioDispatcher(Dispatcher):
    """
    class to hold Eventlistener and the TuioCursors, TuioBlobs, and TuioObjects
    """
    def __init__(self):
        super().__init__()
        self.cursors : List[Cursor] = []
        self.objects : List[Object] = []
        self.blobs   : List[Blob] = []
        self._listener : list = []
        self.map(TUIO_CURSOR, self._cursor_handler)
        self.map(TUIO_OBJECT, self._object_handler)
        self.map(TUIO_BLOB, self._blob_handler)
        self.set_default_handler(self._default_handler)

        self._to_delete = []
        self._to_add    = []
        self._to_update = []

        self._current_source_key = None
        self._frame_alive = {}
        self._frame_sets = {
            TUIO_CURSOR: OrderedDict(),
            TUIO_OBJECT: OrderedDict(),
            TUIO_BLOB: OrderedDict(),
        }

    def _cursor_handler(self, address, *args):
        """
        callback to convert OSC message into TUIO Cursor
        """
        self._profile_handler(TUIO_CURSOR, args)

    def _object_handler(self, address, *args):
        """
        callback to convert OSC message into TUIO Object
        """
        self._profile_handler(TUIO_OBJECT, args)

    def _blob_handler(self, address, *args):
        """
        callback to convert OSC message into TUIO Blob
         """
        self._profile_handler(TUIO_BLOB, args)

    def _profile_handler(self, profile_type, args):
        """Buffer one TUIO profile message until its frame is completed."""
        if len(args) == 0:
            return

        ttype = args[0]
        values = list(args[1:])
        if ttype == TUIO_SOURCE:
            return
        if ttype == TUIO_ALIVE:
            self._handle_alive(profile_type, values)
        elif ttype == TUIO_SET:
            self._handle_set(profile_type, values)
        elif ttype == TUIO_END:
            self._finish_frame(values)

    def _handle_alive(self, profile_type, values):
        """Buffer a validated alive list for the current frame."""
        if not all(type(session_id) is int for session_id in values):
            return
        self._frame_alive[(profile_type, self._current_source_key)] = list(values)

    def _handle_set(self, profile_type, values):
        """Buffer a validated set message for the current frame."""
        decoded = self._decode_set(profile_type, values)
        if decoded is None:
            return
        session_id, state = decoded
        key = (self._current_source_key, session_id)
        self._frame_sets[profile_type][key] = state

    @staticmethod
    def _decode_set(profile_type, values):
        """Decode and type-check one set message without applying it."""
        expected_length = _SET_LENGTHS[profile_type]
        if len(values) < expected_length:
            return None

        values = list(values[:expected_length])
        if type(values[0]) is not int:
            return None

        if profile_type == TUIO_OBJECT:
            if type(values[1]) is not int:
                return None
            float_values = values[2:]
        else:
            float_values = values[1:]

        if not all(type(value) is float for value in float_values):
            return None
        return values[0], tuple(values[1:])

    @staticmethod
    def _profile_state(profile):
        """Return the wire-state tuple for an active profile."""
        if isinstance(profile, Cursor):
            return (
                profile.position[0], profile.position[1],
                profile.velocity[0], profile.velocity[1],
                profile.motion_acceleration,
            )
        if isinstance(profile, Object):
            return (
                profile.class_id,
                profile.position[0], profile.position[1], profile.angle,
                profile.velocity[0], profile.velocity[1],
                profile.velocity_rotation,
                profile.motion_acceleration, profile.rotation_acceleration,
            )
        return (
            profile.position[0], profile.position[1], profile.angle,
            profile.dimension[0], profile.dimension[1], profile.area,
            profile.velocity[0], profile.velocity[1],
            profile.velocity_rotation,
            profile.motion_acceleration, profile.rotation_acceleration,
        )

    @staticmethod
    def _apply_profile_state(profile, state):
        """Apply one decoded wire-state tuple to a profile instance."""
        if isinstance(profile, Cursor):
            profile.position = (state[0], state[1])
            profile.velocity = (state[2], state[3])
            profile.motion_acceleration = state[4]
        elif isinstance(profile, Object):
            profile.class_id = state[0]
            profile.position = (state[1], state[2])
            profile.angle = state[3]
            profile.velocity = (state[4], state[5])
            profile.velocity_rotation = state[6]
            profile.motion_acceleration = state[7]
            profile.rotation_acceleration = state[8]
        else:
            profile.position = (state[0], state[1])
            profile.angle = state[2]
            profile.dimension = (state[3], state[4])
            profile.area = state[5]
            profile.velocity = (state[6], state[7])
            profile.velocity_rotation = state[8]
            profile.motion_acceleration = state[9]
            profile.rotation_acceleration = state[10]

    def _finish_frame(self, values):
        """Apply pending state when an fseq message completes a frame."""
        if len(values) == 0 or type(values[0]) is not int:
            return

        source_key = self._current_source_key
        for profile_type in _PROFILE_ORDER:
            self._process_profile_frame(profile_type, source_key)
        self._call_listener()

    def _process_profile_frame(self, profile_type, source_key):
        """Apply pending alive and set state for one profile/source."""
        alive_key = (profile_type, source_key)
        alive = self._frame_alive.pop(alive_key, _NO_ALIVE)

        set_messages = []
        frame_sets = self._frame_sets[profile_type]
        for key in list(frame_sets.keys()):
            if key[0] == source_key:
                set_messages.append((key[1], frame_sets.pop(key)))

        if alive is _NO_ALIVE and not set_messages:
            return

        active_profiles = self._active_profiles(profile_type)
        if alive is not _NO_ALIVE:
            alive_ids = set(alive)
            for profile in list(active_profiles):
                if self._profile_source_key(profile) != source_key:
                    continue
                if profile.session_id not in alive_ids:
                    active_profiles.remove(profile)
                    self._to_delete.append(profile)

        for session_id, state in set_messages:
            profile = self._find_profile(active_profiles, source_key, session_id)
            if profile is None:
                profile = self._new_profile(profile_type, session_id)
                profile._tuio_source_key = source_key
                self._apply_profile_state(profile, state)
                active_profiles.append(profile)
                self._to_add.append(profile)
            elif self._profile_state(profile) != state:
                self._apply_profile_state(profile, state)
                self._to_update.append(profile)

    def _active_profiles(self, profile_type):
        """Return the public active-profile list for a TUIO profile type."""
        if profile_type == TUIO_CURSOR:
            return self.cursors
        if profile_type == TUIO_OBJECT:
            return self.objects
        return self.blobs

    @staticmethod
    def _new_profile(profile_type, session_id):
        """Create one profile instance for a decoded set message."""
        if profile_type == TUIO_CURSOR:
            return Cursor(session_id)
        if profile_type == TUIO_OBJECT:
            return Object(session_id)
        return Blob(session_id)

    @staticmethod
    def _profile_source_key(profile):
        """Return the internal source key of an active profile."""
        return getattr(profile, "_tuio_source_key", None)

    @classmethod
    def _find_profile(cls, active_profiles, source_key, session_id):
        """Find one active profile by internal source key and session ID."""
        for profile in active_profiles:
            if cls._profile_source_key(profile) == source_key and profile.session_id == session_id:
                return profile
        return None

    def _call_listener(self):    # pylint: disable=R0912
        to_add = self._to_add
        to_update = self._to_update
        to_delete = self._to_delete
        self._to_add = []
        self._to_update = []
        self._to_delete = []

        for listner in self._listener.copy():
            for profile in to_add:
                if  isinstance(profile, Cursor) :
                    listner.add_tuio_cursor(profile)
                elif isinstance(profile, Object) :
                    listner.add_tuio_object(profile)
                elif isinstance(profile, Blob) :
                    listner.add_tuio_blob(profile)

            for profile in to_update:
                if  isinstance(profile, Cursor) :
                    listner.update_tuio_cursor(profile)
                elif isinstance(profile, Object) :
                    listner.update_tuio_object(profile)
                elif isinstance(profile, Blob) :
                    listner.update_tuio_blob(profile)


            for profile in to_delete:
                if  isinstance(profile, Cursor) :
                    listner.remove_tuio_cursor(profile)
                elif isinstance(profile, Object) :
                    listner.remove_tuio_object(profile)
                elif isinstance(profile, Blob) :
                    listner.remove_tuio_blob(profile)

            listner.refresh(0) # TODO implement time conzept pylint


    def add_listener(self, listener :TuioListener):
        """
        Adds the provided TuioListener to the list of registered TUIO event listeners
        """
        self._listener.append(listener)

    def remove_listener(self, listener :TuioListener):
        """
        Removes the provided TuioListener from the list of registered TUIO event listeners
        """
        self._listener.remove(listener)

    def remove_all_listeners(self):
        """
        Removes all provided TuioListeners from the list of registered TUIO event listeners
        """
        self._listener.clear()
