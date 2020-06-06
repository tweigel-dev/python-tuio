from abc import ABC # abstract base class of python

from pythonosc.dispatcher import Dispatcher

from pythontuio import Cursor, Blob, Object
from pythontuio import TUIO_BLOB, TUIO_CURSOR, TUIO_OBJECT

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
        self.map(f"{TUIO_CURSOR}*", _cursor_handler)
        self.map(f"{TUIO_OBJECT}*", _object_handler)
        self.map(f"{TUIO_BLOB}*", _blob_handler)
        self.set_default_handler(_default_handler)

def _cursor_handler(address, *args):
    # cursor = Cursor()
    print(f"{address}: {args}")
    pass
def _object_handler(address, *args):
    print("object")
    pass
def _blob_handler(address, *args):
    pass
def _default_handler(address, *args):
    pass    

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
        pass
# pylint: enable=unnecessary-pass