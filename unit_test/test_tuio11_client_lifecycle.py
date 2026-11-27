import socket
import threading
import time
import unittest

from pythontuio import Cursor, TuioClient, TuioListener, TuioServer


def free_port():
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    return port


def wait_for(predicate, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return predicate()


def send_cursor(port, session_id=1, xpos=0.5):
    """Send one frame keeping the given cursor alive."""
    server = TuioServer("127.0.0.1", port)
    cursor = Cursor(session_id)
    cursor.position = (xpos, 0.5)
    cursor.velocity = (0.0, 0.0)
    cursor.motion_acceleration = 0.0
    server.cursors.append(cursor)
    server.send_bundle()


class QuietListener(TuioListener):
    def __init__(self):
        self.added = []
        self.removed = []

    def add_tuio_cursor(self, cur):
        self.added.append(cur.session_id)

    def remove_tuio_cursor(self, cur):
        self.removed.append(cur.session_id)


class Tuio11ClientLifecycleTest(unittest.TestCase):
    def test_nonblocking_start_receives_and_stops(self):
        port = free_port()
        client = TuioClient(("127.0.0.1", port))
        listener = QuietListener()
        client.add_listener(listener)

        started = time.monotonic()
        client.start(blocking=False)
        self.assertLess(time.monotonic() - started, 0.5)
        self.assertTrue(client.connected)
        self.assertIsNotNone(client._thread)
        self.assertFalse(client._thread.daemon)

        send_cursor(port)
        self.assertTrue(wait_for(lambda: 1 in listener.added))

        stopped = time.monotonic()
        client.stop()
        self.assertLess(time.monotonic() - stopped, 0.5)
        self.assertFalse(client.connected)
        self.assertIsNone(client._thread)

    def test_blocking_start_in_user_thread_can_be_stopped(self):
        port = free_port()
        client = TuioClient(("127.0.0.1", port))
        listener = QuietListener()
        client.add_listener(listener)

        thread = threading.Thread(target=client.start, daemon=True)
        thread.start()
        self.assertTrue(wait_for(lambda: client.connected))
        self.assertTrue(thread.is_alive())

        send_cursor(port)
        self.assertTrue(wait_for(lambda: 1 in listener.added))

        client.stop()
        thread.join(timeout=2.0)
        self.assertFalse(thread.is_alive())
        self.assertFalse(client.connected)

    def test_stop_before_start_and_repeated_stop_are_noops(self):
        client = TuioClient(("127.0.0.1", free_port()))
        client.stop()
        client.stop()
        self.assertFalse(client.connected)

    def test_double_start_raises(self):
        port = free_port()
        client = TuioClient(("127.0.0.1", port))
        client.start(blocking=False)
        try:
            with self.assertRaises(RuntimeError):
                client.start(blocking=False)
            with self.assertRaises(RuntimeError):
                client.start()
        finally:
            client.stop()

    def test_stop_clears_state_silently_and_restart_receives(self):
        port = free_port()
        client = TuioClient(("127.0.0.1", port))
        listener = QuietListener()
        client.add_listener(listener)

        client.start(blocking=False)
        send_cursor(port)
        self.assertTrue(wait_for(lambda: len(client.cursors) == 1))

        removes_before = len(listener.removed)
        client.stop()
        self.assertEqual(client.cursors, [])
        self.assertEqual(len(listener.removed), removes_before)

        port2 = free_port()
        client.server_address = ("127.0.0.1", port2)
        client.start(blocking=False)
        self.assertTrue(client.connected)
        send_cursor(port2, session_id=7)
        self.assertTrue(wait_for(lambda: 7 in listener.added))
        client.stop()
        self.assertFalse(client.connected)

    def test_bind_conflict_raises_and_stays_disconnected(self):
        port = free_port()
        first = TuioClient(("127.0.0.1", port))
        first.start(blocking=False)
        try:
            second = TuioClient(("127.0.0.1", port))
            with self.assertRaises(OSError):
                second.start(blocking=False)
            self.assertFalse(second.connected)
        finally:
            first.stop()

    def test_stop_from_listener_callback_raises_without_deadlock(self):
        port = free_port()
        client = TuioClient(("127.0.0.1", port))

        class StoppingListener(QuietListener):
            def __init__(self):
                super().__init__()
                self.stop_error = None

            def refresh(self, time):
                if self.stop_error is None:
                    try:
                        client.stop()
                        self.stop_error = "no error"
                    except RuntimeError:
                        self.stop_error = "RuntimeError"

        listener = StoppingListener()
        client.add_listener(listener)
        client.start(blocking=False)
        send_cursor(port)
        self.assertTrue(wait_for(lambda: listener.stop_error is not None))
        self.assertEqual(listener.stop_error, "RuntimeError")
        self.assertTrue(client.connected)
        client.stop()
        self.assertFalse(client.connected)

    def test_wildcard_bind_stops_cleanly(self):
        port = free_port()
        client = TuioClient(("0.0.0.0", port))
        client.start(blocking=False)
        self.assertTrue(wait_for(lambda: client.connected))
        client.stop()
        self.assertFalse(client.connected)

    def test_no_receiver_threads_remain(self):
        time.sleep(0.1)
        names = [t.name for t in threading.enumerate()]
        self.assertNotIn("tuio-client-receiver", names)


if __name__ == "__main__":
    unittest.main()
