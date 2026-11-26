import unittest

from pythontuio.dispatcher import TuioDispatcher, TuioListener


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


class Tuio11ClientDispatchTest(unittest.TestCase):
    def test_all_listeners_receive_frame_events(self):
        dispatcher = TuioDispatcher()
        first = RecordingListener()
        second = RecordingListener()
        dispatcher.add_listener(first)
        dispatcher.add_listener(second)

        dispatcher._cursor_handler("/tuio/2Dcur", "alive", 1)
        dispatcher._cursor_handler("/tuio/2Dcur", "set", 1, 0.1, 0.2, 0.0, 0.0, 0.0)
        dispatcher._cursor_handler("/tuio/2Dcur", "fseq", 1)

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

        import io
        import contextlib
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            dispatcher._cursor_handler("/tuio/2Dcur", "alive")
            dispatcher._cursor_handler("/tuio/2Dcur", "fseq", 1)

        self.assertEqual(output.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
