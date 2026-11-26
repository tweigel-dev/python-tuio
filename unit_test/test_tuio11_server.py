import unittest

from pythonosc.osc_bundle import OscBundle

from pythontuio import Blob, Cursor, Object, TuioServer
from pythontuio.const import TUIO_BLOB, TUIO_CURSOR, TUIO_OBJECT


class CaptureTuioServer(TuioServer):
    def __init__(self):
        super().__init__()
        self.sent = []

    def send(self, content):
        self.sent.append(content)


def bundle_messages(bundle):
    return list(OscBundle(bundle.dgram))


def osc_type_tag(dgram):
    address_end = dgram.index(b"\x00")
    type_start = (address_end + 4) & ~3
    type_end = dgram.index(b"\x00", type_start)
    return dgram[type_start:type_end].decode("ascii")


class Tuio11ServerWireTest(unittest.TestCase):
    def test_existing_api_sends_ordered_profile_bundles_with_shared_fseq(self):
        server = CaptureTuioServer()
        cursor = Cursor(42)
        cursor.position = (0.5, 0.25)
        server.cursors.append(cursor)

        server.send_bundle()

        self.assertEqual(len(server.sent), 3)
        parsed = [bundle_messages(bundle) for bundle in server.sent]
        by_address = {messages[0].address: messages for messages in parsed}

        self.assertEqual(set(by_address), {TUIO_CURSOR, TUIO_OBJECT, TUIO_BLOB})
        for address, messages in by_address.items():
            self.assertTrue(all(message.address == address for message in messages))
            self.assertEqual(messages[0].params[0], "alive")
            self.assertEqual(messages[-1].params, ["fseq", 0])
            for message in messages[1:-1]:
                self.assertEqual(message.params[0], "set")

        cursor_messages = by_address[TUIO_CURSOR]
        self.assertEqual(len(cursor_messages), 3)
        self.assertEqual(cursor_messages[0].params, ["alive", 42])
        self.assertEqual(cursor_messages[1].params[0], "set")

        self.assertEqual(by_address[TUIO_OBJECT][0].params, ["alive"])
        self.assertEqual(by_address[TUIO_BLOB][0].params, ["alive"])

        server.send_bundle()
        second_frame = [bundle_messages(bundle) for bundle in server.sent[3:]]
        self.assertEqual(len(second_frame), 3)
        for messages in second_frame:
            self.assertEqual(messages[-1].params, ["fseq", 1])

    def test_set_messages_use_tuio_wire_types(self):
        server = CaptureTuioServer()

        cursor = Cursor(1)
        cursor.position = (0.1, 0.2)
        server.cursors.append(cursor)

        obj = Object(2)
        obj.class_id = 7
        obj.position = (0.3, 0.4)
        server.objects.append(obj)

        blob = Blob(3)
        blob.position = (0.5, 0.6)
        blob.angle = 0.7
        blob.dimension = (0.2, 0.1)
        blob.area = 0.02
        server.blobs.append(blob)

        server.send_bundle()

        parsed = [bundle_messages(bundle) for bundle in server.sent]
        by_address = {messages[0].address: messages for messages in parsed}
        cursor_set = by_address[TUIO_CURSOR][1]
        object_set = by_address[TUIO_OBJECT][1]
        blob_set = by_address[TUIO_BLOB][1]

        self.assertEqual(osc_type_tag(cursor_set.dgram), ",sifffff")
        self.assertEqual(osc_type_tag(object_set.dgram), ",siiffffffff")
        self.assertEqual(osc_type_tag(blob_set.dgram), ",sifffffffffff")

    def test_empty_alive_and_fseq_wire_types_are_minimal(self):
        server = CaptureTuioServer()

        server.send_bundle()

        for bundle in server.sent:
            messages = bundle_messages(bundle)
            self.assertEqual(len(messages), 2)
            self.assertEqual(osc_type_tag(messages[0].dgram), ",s")
            self.assertEqual(messages[0].params, ["alive"])
            self.assertEqual(osc_type_tag(messages[1].dgram), ",si")
            self.assertEqual(messages[1].params, ["fseq", 0])

    def test_fseq_wraps_within_nonnegative_int32_range(self):
        server = CaptureTuioServer()
        server._fseq = (2**31) - 2

        self.assertEqual(server.next_fseq(), (2**31) - 2)
        self.assertEqual(server.next_fseq(), (2**31) - 1)
        self.assertEqual(server.next_fseq(), 0)


if __name__ == "__main__":
    unittest.main()
