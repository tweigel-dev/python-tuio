"""
classes to handle incoming osc messages
"""
from abc import ABC # abstract base class of python

from pythonosc.dispatcher import Dispatcher

from pythontuio.tuio_profiles import Cursor, Blob, Object
from pythontuio.tuio_profiles import TUIO_BLOB, TUIO_CURSOR, TUIO_OBJECT

from pythontuio.const import TUIO_END,TUIO_ALIVE,TUIO_SET, TUIO_SOURCE
from typing import List


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
        super(TuioDispatcher, self).__init__()
        self.cursors : List(Cursor) = []
        self.objects : List(Object) = []
        self.blobs   : List(Blob) = []
        self._listener : list = []
        self.map(f"{TUIO_CURSOR}*", self._cursor_handler)
        self.map(f"{TUIO_OBJECT}*", self._object_handler)
        self.map(f"{TUIO_BLOB}*", self._blob_handler)
        self.set_default_handler(self._default_handler)

        self._to_delete = []
        self._to_add    = []
        self._to_update = []

    def _cursor_handler(self, address, *args):
        """
        callback to convert OSC message into TUIO Cursor
        """
        if len(args) == 0 :
            raise Exception("TUIO message is Broken. No TUIO type specified")
        ttype = args[0]
        args = list(args[1:])
        if ttype == TUIO_SOURCE:
            pass
            #print(f"Message by {args} reveiced")
        elif ttype == TUIO_ALIVE :
            cursors = self.cursors.copy()
            self.cursors = self._sort_matchs(cursors, args, Cursor)

        elif ttype == TUIO_SET:
            for cursor in self.cursors:
                if cursor.session_id != args[0]:
                    continue
                cursor.position = (args[1], args[2])
                cursor.velocity = (args[3], args[4])
                cursor.motion_acceleration = args[5]


        elif ttype == TUIO_END:
            self._call_listener()
            print(f"Bundle recived with {address}:{ttype} {args}")


        else:
            raise Exception("Broken TUIO Package")


    def _object_handler(self, address, *args):
        """
        callback to convert OSC message into TUIO Object
        """
        if len(args) == 0 :
            raise Exception("TUIO message is Broken. No TUIO type specified")
        ttype = args[0]
        args = list(args[1:])
        if ttype == TUIO_SOURCE:
            #print(f"Message by {args} reveiced")
            pass
        elif ttype == TUIO_ALIVE :
            objects = self.objects.copy()
            self.objects = self._sort_matchs(objects, args, Object)

        elif ttype == TUIO_SET:
            for obj in self.objects:
                if obj.session_id != args[0]:
                    continue
                obj.class_id               = args[1]                # i
                obj.position               = (args[2], args[3])     # x,y
                obj.angle                  = args[4]                # a
                obj.velocity               = (args[5], args[6])     # X,Y
                obj.velocity_rotation      = args[7]                # A
                obj.motion_acceleration    = args[8]                # m
                obj.rotation_acceleration  = args[9]                # r

        
        elif ttype == TUIO_END:
            self._call_listener()
            print(f"Bundle recived with {address}:{ttype} {args}")
        else:
            raise Exception("Broken TUIO Package")

    def _blob_handler(self, address, *args):
        """
        callback to convert OSC message into TUIO Blob
         """

        if len(args) == 0 :
            raise Exception("TUIO message is Broken. No TUIO type specified")
        ttype = args[0]
        args = list(args[1:])
        if ttype == TUIO_SOURCE:
            pass
        elif ttype == TUIO_ALIVE :
            blobs = self.blobs.copy()
            self.blobs = self._sort_matchs(blobs, args, Blob)

        elif ttype == TUIO_SET:
            for blob in self.blobs:
                if blob.session_id != args[0]:
                    continue
                blob.position               = (args[1], args[2])     # x,y
                blob.angle                  = args[3]                # a
                blob.dimension              = (args[4], args[5])     # w, h
                blob.area                   = args[6]                # f
                blob.velocity               = (args[7], args[8])     # X,Y
                blob.velocity_rotation      = args[9]                # A
                blob.motion_acceleration    = args[10]               # m
                blob.rotation_acceleration  = args[11]               # r
               

        elif ttype == TUIO_END:
            self._call_listener()
            print(f"Bundle recived with {address}:{ttype} {args}")
        else:
            raise Exception("Broken TUIO Package")
    
    def _call_listener(self):
        for listner in self._listener:
            for profile in self._to_add:
                if  isinstance(profile, Cursor) :
                    listner.add_tuio_cursor(profile)
                elif isinstance(profile, Object) :
                    listner.add_tuio_object(profile)
                elif isinstance(profile, Blob) :
                    listner.add_tuio_blob(profile)

            for profile in self._to_update:
                if  isinstance(profile, Cursor) :
                    listner.update_tuio_cursor(profile)
                elif isinstance(profile, Object) :
                    listner.update_tuio_object(profile)
                elif isinstance(profile, Blob) :
                    listner.update_tuio_blob(profile)


            for profile in self._to_delete:
                if  isinstance(profile, Cursor) :
                    listner.remove_tuio_cursor(profile)
                elif isinstance(profile, Object) :
                    listner.remove_tuio_object(profile)
                elif isinstance(profile, Blob) :
                    listner.remove_tuio_blob(profile)

            listner.refresh(0) # TODO implement time conzept
            self._to_add    = []
            self._to_update = []
            self._to_delete = []


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

    def _sort_matchs(self, profile_list, session_ids, Profile_type):
        """
        sort incoming session_ids into the lists and fill the listner stacks
        """
        new_profiles = []
        rest_profiles = profile_list.copy()
        rest_sessions = session_ids.copy()

        for session_id in session_ids:
            # search for profile
            for profile in profile_list:
            
                if profile.session_id == session_id:
                    new_profiles.append(profile)
                    self._to_update.append(profile)# add into event list update
                    rest_profiles.remove(profile)
                    rest_sessions.remove(session_id)
           
        for profile in rest_profiles:
            self._to_delete.append(profile)# add into event list delete

        for session_id in rest_sessions:
            profile = Profile_type(session_id)
            new_profiles.append(profile)
            self._to_add.append(profile)# add into event list add

        return new_profiles
