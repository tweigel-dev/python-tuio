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


class RefreshListener(TuioListener):
    def __init__(self):
        self.refreshes = 0
        self.added = []

    def refresh(self, time):
        self.refreshes += 1

    def add_tuio_cursor(self, cur):
        self.added.append(cur.session_id)


class Tuio11PeriodicMessagesTest(unittest.TestCase):
    def make_pair(self):
        port = free_port()
        server = TuioServer("127.0.0.1", port)
        client = TuioClient(("127.0.0.1", port))
        listener = RefreshListener()
        client.add_listener(listener)
        return server, client, listener

    def test_full_update_resyncs_static_scene_without_send_bundle(self):
        server, client, listener = self.make_pair()
        cursor = Cursor(5)
        cursor.position = (0.5, 0.5)
        server.cursors.append(cursor)

        server.is_full_update = True
        server.enable_periodic_messages(50)
        try:
            client.start(blocking=False)
            try:
                # no send_bundle() is ever called by the application
                self.assertTrue(wait_for(lambda: 5 in listener.added))
                self.assertTrue(wait_for(lambda: len(client.cursors) == 1))
            finally:
                client.stop()
        finally:
            server.disable_periodic_messages()

    def test_keepalive_mode_sends_no_set_messages(self):
        server, client, listener = self.make_pair()
        cursor = Cursor(5)
        cursor.position = (0.5, 0.5)
        server.cursors.append(cursor)

        # is_full_update defaults to False: alive-only keepalive bundles
        server.enable_periodic_messages(50)
        try:
            client.start(blocking=False)
            try:
                self.assertTrue(wait_for(lambda: listener.refreshes >= 2))
                time.sleep(0.1)
                # keepalives contain alive but no set messages, so the
                # client must not fabricate any cursor state
                self.assertEqual(client.cursors, [])
                self.assertEqual(listener.added, [])
            finally:
                client.stop()
        finally:
            server.disable_periodic_messages()

    def test_disable_stops_retransmission(self):
        server, client, listener = self.make_pair()
        server.enable_periodic_messages(40)
        client.start(blocking=False)
        try:
            self.assertTrue(wait_for(lambda: listener.refreshes >= 2))
            server.disable_periodic_messages()
            time.sleep(0.1)  # drain packets already in flight
            count = listener.refreshes
            time.sleep(0.2)  # five intervals without new messages
            self.assertEqual(listener.refreshes, count)
            self.assertFalse(server.periodic_messages_enabled())
        finally:
            client.stop()
            server.disable_periodic_messages()

    def test_repeated_enable_disable_and_idempotent_disable(self):
        server, client, listener = self.make_pair()
        server.disable_periodic_messages()  # no-op before first enable
        for _ in range(3):
            server.enable_periodic_messages(40)
            self.assertTrue(server.periodic_messages_enabled())
            server.disable_periodic_messages()
            self.assertFalse(server.periodic_messages_enabled())
        server.disable_periodic_messages()
        self.assertIsNone(server._periodic_thread)

    def test_invalid_interval_raises(self):
        server = TuioServer()
        with self.assertRaises(ValueError):
            server.enable_periodic_messages(0)
        with self.assertRaises(ValueError):
            server.enable_periodic_messages(-5)
        self.assertFalse(server.periodic_messages_enabled())

    def test_redundant_frames_do_not_advance_client_sequence(self):
        server, client, listener = self.make_pair()
        cursor = Cursor(5)
        cursor.position = (0.5, 0.5)
        server.cursors.append(cursor)
        server.is_full_update = True
        server.enable_periodic_messages(40)
        try:
            client.start(blocking=False)
            try:
                self.assertTrue(wait_for(lambda: 5 in listener.added))
                # many redundant frames are processed without errors
                self.assertTrue(wait_for(lambda: listener.refreshes >= 6))
                self.assertEqual(len(client.cursors), 1)
            finally:
                client.stop()
        finally:
            server.disable_periodic_messages()

    def test_no_periodic_threads_remain(self):
        time.sleep(0.1)
        names = [t.name for t in threading.enumerate()]
        self.assertNotIn("tuio-server-periodic", names)


if __name__ == "__main__":
    unittest.main()
