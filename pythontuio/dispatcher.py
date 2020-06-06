"""
classes to handle incoming osc messages
"""
from abc import ABC # abstract base class of python

from pythonosc.dispatcher import Dispatcher

from pythontuio.tuio_profiles import Cursor, Blob, Object
from pythontuio.tuio_profiles import TUIO_BLOB, TUIO_CURSOR, TUIO_OBJECT

from pythontuio.const import TUIO_END,TUIO_ALIVE,TUIO_SET, TUIO_SOURCE



class TuioDispatcher(Dispatcher):
    """
    class to hold Eventlistener and the TuioCursors, TuioBlobs, and TuioObjects
    """
    def __init__(self):
        super(TuioDispatcher, self).__init__()
        self.cursors : list = []
        self.objects : list = []
        self.blobs   : list = []
        self.listener : list = []
        self.map(f"{TUIO_CURSOR}*", self._cursor_handler)
        self.map(f"{TUIO_OBJECT}*", self._object_handler)
        self.map(f"{TUIO_BLOB}*", self._blob_handler)
        self.set_default_handler(self._default_handler)

    def _cursor_handler(self, address, ttype, *args):
        cursor = None
        print(f"{address}:{ttype} {args}")
        if ttype == TUIO_ALIVE :
            cursors = self.cursors.copy()
            new_cursors = []
            for session_id in args:
                cursor_match = None
                # search for cursor
                for cursor in cursors:
                    if cursor.session_id == session_id:
                        cursor_match = cursor
                # if match found copy it
                if cursor_match is not None:
                    new_cursors.append(cursor_match)
                # else add new one
                else :
                    new_cursors.append(Cursor(session_id))
            self.cursors = new_cursors

        elif ttype == TUIO_SET:
            for cursor in self.cursors:
                if cursor.session_id != args[0]:
                    continue
                cursor.position = (args[1], args[2])
                cursor.velocity = (args[3], args[4])
                cursor.motion_acceleration = args[5]

        elif ttype == TUIO_END:
            return # nothing to happend here
        elif ttype == TUIO_SOURCE:
            print(f"Message by {args} reveiced")
        else:
            raise Exception("Broken TUIO Package")


    def _object_handler(self, address, ttype, *args):
        raise NotImplementedError()

    def _blob_handler(self, address, ttype, *args):
        raise NotImplementedError()


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