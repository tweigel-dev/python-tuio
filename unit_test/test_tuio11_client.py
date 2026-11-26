import contextlib
import io
import unittest

from pythontuio.dispatcher import TuioDispatcher, TuioListener


CURSOR_SET = (1, 0.1, 0.2, 0.3, 0.4, 0.5)
OBJECT_SET = (2, 7, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8)
BLOB_SET = (3, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1)


class RecordingListener(TuioListener):
    def __init__(self):
        self.events = []

    def add_tuio_object(self, obj):
        self.events.append(("add_obj", obj.session_id))

    def update_tuio_object(self, obj):
        self.events.append(("update_obj", obj.session_id))

    def remove_tuio_object(self, obj):
        self.events.append(("remove_obj", obj.session_id))

    def add_tuio_cursor(self, cur):
        self.events.append(("add_cur", cur.session_id))

    def update_tuio_cursor(self, cur):
        self.events.append(("update_cur", cur.session_id))

    def remove_tuio_cursor(self, cur):
        self.events.append(("remove_cur", cur.session_id))

    def add_tuio_blob(self, blob):
        self.events.append(("add_blob", blob.session_id))

    def update_tuio_blob(self, blob):
        self.events.append(("update_blob", blob.session_id))

    def remove_tuio_blob(self, blob):
        self.events.append(("remove_blob", blob.session_id))

    def refresh(self, time):
        self.events.append(("refresh", time))


def cursor_frame(dispatcher, session_id=1, values=CURSOR_SET[1:], fseq=1, alive_ids=None):
    if alive_ids is None:
        alive_ids = [session_id]
    dispatcher._cursor_handler("/tuio/2Dcur", "alive", *alive_ids)
    if values is not None:
        dispatcher._cursor_handler("/tuio/2Dcur", "set", session_id, *values)
    dispatcher._cursor_handler("/tuio/2Dcur", "fseq", fseq)


class Tuio11ClientDispatchTest(unittest.TestCase):
    def test_all_listeners_receive_frame_events(self):
        dispatcher = TuioDispatcher()
        first = RecordingListener()
        second = RecordingListener()
        dispatcher.add_listener(first)
        dispatcher.add_listener(second)

        cursor_frame(dispatcher)

        self.assertEqual(first.events, second.events)
        self.assertIn(("add_cur", 1), first.events)
        self.assertIn(("refresh", 0), first.events)

    def test_events_are_cleared_without_listeners(self):
        dispatcher = TuioDispatcher()

        dispatcher._cursor_handler("/tuio/2Dcur", "alive", 1)
        dispatcher._cursor_handler("/tuio/2Dcur", "fseq", 1)

        self.assertEqual(dispatcher._to_add, [])
        self.assertEqual(dispatcher._to_update, [])
        self.assertEqual(dispatcher._to_delete, [])

    def test_fseq_does_not_print_debug_output(self):
        dispatcher = TuioDispatcher()
        dispatcher.add_listener(RecordingListener())

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            dispatcher._cursor_handler("/tuio/2Dcur", "alive")
            dispatcher._cursor_handler("/tuio/2Dcur", "fseq", 1)

        self.assertEqual(output.getvalue(), "")

    def test_cursor_state_is_atomic_at_fseq_and_decoded_exactly(self):
        dispatcher = TuioDispatcher()
        listener = RecordingListener()
        dispatcher.add_listener(listener)

        dispatcher._cursor_handler("/tuio/2Dcur", "alive", 1)
        dispatcher._cursor_handler("/tuio/2Dcur", "set", *CURSOR_SET)
        self.assertEqual(dispatcher.cursors, [])
        self.assertEqual(listener.events, [])

        dispatcher._cursor_handler("/tuio/2Dcur", "fseq", 1)

        self.assertEqual(len(dispatcher.cursors), 1)
        cursor = dispatcher.cursors[0]
        self.assertEqual(cursor.session_id, 1)
        self.assertEqual(cursor.position, (0.1, 0.2))
        self.assertEqual(cursor.velocity, (0.3, 0.4))
        self.assertEqual(cursor.motion_acceleration, 0.5)
        self.assertEqual(listener.events, [("add_cur", 1), ("refresh", 0)])

    def test_object_and_blob_fields_are_decoded_exactly(self):
        dispatcher = TuioDispatcher()

        dispatcher._object_handler("/tuio/2Dobj", "alive", 2)
        dispatcher._object_handler("/tuio/2Dobj", "set", *OBJECT_SET)
        dispatcher._object_handler("/tuio/2Dobj", "fseq", 1)
        obj = dispatcher.objects[0]
        self.assertEqual(obj.class_id, 7)
        self.assertEqual(obj.position, (0.1, 0.2))
        self.assertEqual(obj.angle, 0.3)
        self.assertEqual(obj.velocity, (0.4, 0.5))
        self.assertEqual(obj.velocity_rotation, 0.6)
        self.assertEqual(obj.motion_acceleration, 0.7)
        self.assertEqual(obj.rotation_acceleration, 0.8)

        dispatcher._blob_handler("/tuio/2Dblb", "alive", 3)
        dispatcher._blob_handler("/tuio/2Dblb", "set", *BLOB_SET)
        dispatcher._blob_handler("/tuio/2Dblb", "fseq", 1)
        blob = dispatcher.blobs[0]
        self.assertEqual(blob.position, (0.1, 0.2))
        self.assertEqual(blob.angle, 0.3)
        self.assertEqual(blob.dimension, (0.4, 0.5))
        self.assertEqual(blob.area, 0.6)
        self.assertEqual(blob.velocity, (0.7, 0.8))
        self.assertEqual(blob.velocity_rotation, 0.9)
        self.assertEqual(blob.motion_acceleration, 1.0)
        self.assertEqual(blob.rotation_acceleration, 1.1)

    def test_unchanged_alive_does_not_create_spurious_update(self):
        dispatcher = TuioDispatcher()
        listener = RecordingListener()
        dispatcher.add_listener(listener)

        cursor_frame(dispatcher, fseq=1)
        listener.events.clear()
        cursor_frame(dispatcher, fseq=2)

        self.assertEqual(listener.events, [("refresh", 0)])
        self.assertEqual(len(dispatcher.cursors), 1)

    def test_changed_set_updates_existing_profile_instance(self):
        dispatcher = TuioDispatcher()
        listener = RecordingListener()
        dispatcher.add_listener(listener)

        cursor_frame(dispatcher, fseq=1)
        cursor = dispatcher.cursors[0]
        listener.events.clear()
        cursor_frame(dispatcher, values=(0.9, 0.2, 0.3, 0.4, 0.5), fseq=2)

        self.assertIs(dispatcher.cursors[0], cursor)
        self.assertEqual(cursor.position, (0.9, 0.2))
        self.assertEqual(listener.events, [("update_cur", 1), ("refresh", 0)])

    def test_removal_requires_alive_message(self):
        dispatcher = TuioDispatcher()
        listener = RecordingListener()
        dispatcher.add_listener(listener)

        cursor_frame(dispatcher, fseq=1)
        listener.events.clear()

        dispatcher._cursor_handler("/tuio/2Dcur", "set", *CURSOR_SET)
        dispatcher._cursor_handler("/tuio/2Dcur", "fseq", 2)
        self.assertEqual(len(dispatcher.cursors), 1)
        self.assertNotIn(("remove_cur", 1), listener.events)

        dispatcher._cursor_handler("/tuio/2Dcur", "alive")
        dispatcher._cursor_handler("/tuio/2Dcur", "fseq", 3)
        self.assertEqual(dispatcher.cursors, [])
        self.assertIn(("remove_cur", 1), listener.events)

    def test_blob_rotation_only_update_is_not_deduplicated_away(self):
        dispatcher = TuioDispatcher()
        listener = RecordingListener()
        dispatcher.add_listener(listener)

        dispatcher._blob_handler("/tuio/2Dblb", "alive", 3)
        dispatcher._blob_handler("/tuio/2Dblb", "set", *BLOB_SET)
        dispatcher._blob_handler("/tuio/2Dblb", "fseq", 1)
        listener.events.clear()

        rotated = list(BLOB_SET)
        rotated[-3] = 0.25
        rotated[-1] = 0.125
        dispatcher._blob_handler("/tuio/2Dblb", "alive", 3)
        dispatcher._blob_handler("/tuio/2Dblb", "set", *rotated)
        dispatcher._blob_handler("/tuio/2Dblb", "fseq", 2)

        self.assertEqual(listener.events, [("update_blob", 3), ("refresh", 0)])
        self.assertEqual(dispatcher.blobs[0].velocity_rotation, 0.25)
        self.assertEqual(dispatcher.blobs[0].rotation_acceleration, 0.125)

    def test_split_packets_with_same_fseq_are_accepted(self):
        dispatcher = TuioDispatcher()
        listener = RecordingListener()
        dispatcher.add_listener(listener)

        cursor_frame(dispatcher, session_id=10, fseq=5, alive_ids=[10])
        cursor_frame(dispatcher, session_id=11, fseq=5, alive_ids=[10, 11])

        self.assertEqual([cursor.session_id for cursor in dispatcher.cursors], [10, 11])
        self.assertEqual(
            listener.events.count(("refresh", 0)),
            2,
        )

    def test_older_fseq_is_dropped_without_events_or_refresh(self):
        dispatcher = TuioDispatcher()
        listener = RecordingListener()
        dispatcher.add_listener(listener)

        cursor_frame(dispatcher, session_id=10, fseq=5, alive_ids=[10])
        listener.events.clear()

        cursor_frame(dispatcher, session_id=12, fseq=3, alive_ids=[10, 12])

        self.assertEqual([cursor.session_id for cursor in dispatcher.cursors], [10])
        self.assertEqual(listener.events, [])

    def test_redundant_fseq_minus_one_is_processed(self):
        dispatcher = TuioDispatcher()
        listener = RecordingListener()
        dispatcher.add_listener(listener)

        cursor_frame(dispatcher, session_id=10, fseq=5, alive_ids=[10])
        listener.events.clear()

        dispatcher._cursor_handler("/tuio/2Dcur", "alive", 10)
        dispatcher._cursor_handler("/tuio/2Dcur", "fseq", -1)

        self.assertEqual([cursor.session_id for cursor in dispatcher.cursors], [10])
        self.assertEqual(listener.events, [("refresh", 0)])

    def test_large_backwards_jump_is_accepted_as_sequence_wraparound(self):
        dispatcher = TuioDispatcher()

        cursor_frame(dispatcher, session_id=10, fseq=200, alive_ids=[10])
        cursor_frame(dispatcher, session_id=10, fseq=50, alive_ids=[10])
        self.assertEqual(len(dispatcher.cursors), 1)

        listener = RecordingListener()
        dispatcher.add_listener(listener)
        cursor_frame(dispatcher, session_id=11, fseq=49, alive_ids=[10, 11])
        self.assertEqual(listener.events, [])
        self.assertEqual([cursor.session_id for cursor in dispatcher.cursors], [10])

    def test_malformed_messages_are_ignored_without_breaking_frame(self):
        dispatcher = TuioDispatcher()
        listener = RecordingListener()
        dispatcher.add_listener(listener)

        dispatcher._cursor_handler("/tuio/2Dcur")
        dispatcher._cursor_handler("/tuio/2Dcur", "bogus", 1)
        dispatcher._cursor_handler("/tuio/2Dcur", "alive", 1)
        dispatcher._cursor_handler("/tuio/2Dcur", "set", 1, 0.1)
        dispatcher._cursor_handler("/tuio/2Dcur", "set", 1.0, 0.1, 0.2, 0.0, 0.0, 0.0)
        dispatcher._cursor_handler("/tuio/2Dcur", "set", 1, 1, 0.2, 0.0, 0.0, 0.0)
        dispatcher._cursor_handler("/tuio/2Dcur", "fseq", 1)

        self.assertEqual(dispatcher.cursors, [])
        self.assertEqual(listener.events, [("refresh", 0)])

    def test_surplus_set_arguments_are_tolerated(self):
        dispatcher = TuioDispatcher()

        dispatcher._cursor_handler("/tuio/2Dcur", "alive", 1)
        dispatcher._cursor_handler("/tuio/2Dcur", "set", *CURSOR_SET, 3.14)
        dispatcher._cursor_handler("/tuio/2Dcur", "fseq", 1)

        self.assertEqual(len(dispatcher.cursors), 1)
        self.assertEqual(dispatcher.cursors[0].position, (0.1, 0.2))

    def test_legacy_mixed_profile_frame_is_flushed_by_cursor_fseq(self):
        dispatcher = TuioDispatcher()

        dispatcher._object_handler("/tuio/2Dobj", "alive", 2)
        dispatcher._object_handler("/tuio/2Dobj", "set", *OBJECT_SET)
        dispatcher._blob_handler("/tuio/2Dblb", "alive", 3)
        dispatcher._blob_handler("/tuio/2Dblb", "set", *BLOB_SET)
        dispatcher._cursor_handler("/tuio/2Dcur", "alive", 1)
        dispatcher._cursor_handler("/tuio/2Dcur", "set", *CURSOR_SET)
        dispatcher._cursor_handler("/tuio/2Dcur", "fseq", 1)

        self.assertEqual(len(dispatcher.objects), 1)
        self.assertEqual(len(dispatcher.blobs), 1)
        self.assertEqual(len(dispatcher.cursors), 1)


if __name__ == "__main__":
    unittest.main()
