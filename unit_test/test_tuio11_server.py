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

    def test_source_message_is_optional_and_first(self):
        server = CaptureTuioServer()
        server.set_source_name(_name="test-source")

        server.send_bundle()

        for bundle in server.sent:
            messages = bundle_messages(bundle)
            self.assertEqual(messages[0].params, ["source", "test-source"])
            self.assertEqual(osc_type_tag(messages[0].dgram), ",ss")
            self.assertEqual(messages[1].params[0], "alive")

        addressed = CaptureTuioServer()
        addressed.set_source_name("test-source", "10.0.0.1")
        addressed.send_bundle()
        first = bundle_messages(addressed.sent[0])[0]
        self.assertEqual(first.params, ["source", "test-source@10.0.0.1"])

    def test_profile_enablement_controls_send_bundle_output(self):
        server = CaptureTuioServer()

        self.assertTrue(server.has_cursor_profile())
        self.assertTrue(server.has_object_profile())
        self.assertTrue(server.has_blob_profile())

        server.enable_object_profile(False)
        server.enable_blob_profile(False)
        server.send_bundle()

        self.assertFalse(server.has_object_profile())
        self.assertFalse(server.has_blob_profile())
        self.assertEqual(len(server.sent), 1)
        self.assertEqual(bundle_messages(server.sent[0])[0].address, TUIO_CURSOR)

        server.enable_object_profile()
        server.send_bundle()
        self.assertEqual(len(server.sent), 3)

    def test_send_full_messages_uses_minus_one_without_advancing_fseq(self):
        server = CaptureTuioServer()
        cursor = Cursor(42)
        server.cursors.append(cursor)

        server.send_full_messages()

        self.assertEqual(len(server.sent), 3)
        for bundle in server.sent:
            messages = bundle_messages(bundle)
            self.assertEqual(messages[-1].params, ["fseq", -1])
        cursor_messages = bundle_messages(server.sent[0])
        self.assertEqual(cursor_messages[1].params[0], "set")
        self.assertEqual(server.next_fseq(), 0)

    def test_empty_profile_bundles_use_minus_one(self):
        server = CaptureTuioServer()

        server.send_empty_cursor_bundle()
        server.send_empty_object_bundle()
        server.send_empty_blob_bundle()

        addresses = []
        for bundle in server.sent:
            messages = bundle_messages(bundle)
            addresses.append(messages[0].address)
            self.assertEqual(len(messages), 2)
            self.assertEqual(messages[0].params, ["alive"])
            self.assertEqual(messages[1].params, ["fseq", -1])
        self.assertEqual(addresses, [TUIO_CURSOR, TUIO_OBJECT, TUIO_BLOB])

    def test_send_profile_bundle_separates_alive_and_updated_profiles(self):
        server = CaptureTuioServer()
        active = [Cursor(1), Cursor(2)]
        updated = [active[1]]

        used_fseq = server.send_profile_bundle(
            TUIO_CURSOR,
            active,
            updated,
            fseq=7,
        )

        self.assertEqual(used_fseq, 7)
        messages = bundle_messages(server.sent[0])
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0].params, ["alive", 1, 2])
        self.assertEqual(messages[1].params[0], "set")
        self.assertEqual(messages[1].params[1], 2)
        self.assertEqual(messages[2].params, ["fseq", 7])

    def test_send_profile_bundle_defaults_to_full_active_state_and_auto_fseq(self):
        server = CaptureTuioServer()
        active = [Cursor(1)]

        used_fseq = server.send_profile_bundle(TUIO_CURSOR, active)

        self.assertEqual(used_fseq, 0)
        messages = bundle_messages(server.sent[0])
        self.assertEqual(messages[0].params, ["alive", 1])
        self.assertEqual(messages[1].params[0], "set")
        self.assertEqual(messages[2].params, ["fseq", 0])


if __name__ == "__main__":
    unittest.main()
