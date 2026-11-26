# python-tuio

`python-tuio` is a Python 3 implementation of the TUIO 1.1 protocol using OSC over UDP. It is implemented with the [`python-osc`](https://python-osc.readthedocs.io/) library.

The library supports the standard two-dimensional TUIO profiles:

- `/tuio/2Dobj` — tangible objects
- `/tuio/2Dcur` — touch or pointer cursors
- `/tuio/2Dblb` — untracked blobs

References:

- [TUIO specification](https://www.tuio.org/?specification)
- [TUIO C++ reference implementation](https://www.tuio.org/?cpp)
- [OSC 1.0 specification](https://opensoundcontrol.org/spec-1_0)

## Installation

```sh
pip3 install python-tuio
```

## Server usage

The existing server API is state-oriented: create profile instances, place them in the public `cursors`, `objects`, or `blobs` lists, update their attributes, and call `send_bundle()` for each frame.

```python
import time

from pythontuio import Cursor, TuioServer

server = TuioServer()  # defaults to 127.0.0.1:3333
cursor = Cursor(123)   # session ID 123

server.cursors.append(cursor)

for index in range(10):
    cursor.position = (0.5 + 0.01 * index, 0.5)
    cursor.velocity = (0.2, 0.1)
    cursor.motion_acceleration = 0.1
    server.send_bundle()
    time.sleep(0.1)
```

`Object` instances additionally provide `class_id`, `angle`, `velocity_rotation`, and `rotation_acceleration`. `Blob` instances additionally provide `angle`, `dimension`, `area`, `velocity_rotation`, and `rotation_acceleration`.

### Server wire behavior

`send_bundle()` emits TUIO 1.1-compliant, profile-specific OSC bundles. Each enabled profile is sent in its own bundle ordered as:

1. optional `source`
2. `alive`
3. zero or more `set` messages
4. concluding `fseq`

Bundles belonging to the same `send_bundle()` call share the same incrementing nonnegative frame sequence ID. Empty enabled profiles are still represented by minimal `alive`/`fseq` bundles so receivers can observe removals.

An optional source name can identify the sending application:

```python
server.set_source_name("my_application")
# or explicitly:
server.set_source_name("my_application", "192.168.1.10")
```

All three standard profiles are enabled by default for backwards compatibility. Applications that only use selected profiles can disable the others:

```python
server.enable_object_profile(False)
server.enable_blob_profile(False)

print(server.has_cursor_profile())
print(server.has_object_profile())
print(server.has_blob_profile())
```

`send_full_messages()` resends the complete state of all enabled profiles with the redundant frame marker `fseq -1`. Explicit empty bundles are available for startup or shutdown state clearing:

```python
server.send_full_messages()
server.send_empty_cursor_bundle()
server.send_empty_object_bundle()
server.send_empty_blob_bundle()
```

### Advanced server frame control

Frame-driven transmitters can use `send_profile_bundle()` to send a complete `alive` list while including only changed profiles in the `set` messages. Use the same frame sequence for profiles belonging to one acquisition frame:

```python
fseq = server.next_fseq()
server.send_profile_bundle("/tuio/2Dcur", active_cursors, changed_cursors, fseq=fseq)
server.send_profile_bundle("/tuio/2Dblb", active_blobs, changed_blobs, fseq=fseq)
```

If `set_profiles` or `fseq` are omitted, `send_profile_bundle()` sends all active profiles and allocates the next frame sequence automatically.

The server does not currently split very large frames across multiple UDP packets or schedule periodic retransmission itself. Frame-driven applications remain responsible for calling `send_bundle()` or `send_full_messages()` at the desired rate. The periodic-message methods remain unimplemented and raise an exception.

## Client usage

Implement the callback methods needed by your application in a `TuioListener` subclass and register it with a `TuioClient`.

```python
from threading import Thread

from pythontuio import Cursor, TuioClient, TuioListener

class MyListener(TuioListener):
    def add_tuio_cursor(self, cursor: Cursor):
        print("added cursor", cursor.session_id)

    def update_tuio_cursor(self, cursor: Cursor):
        print("cursor", cursor.session_id, cursor.position)

    def remove_tuio_cursor(self, cursor: Cursor):
        print("removed cursor", cursor.session_id)

    def refresh(self, time):
        pass

client = TuioClient(("localhost", 3333))
client.add_listener(MyListener())

# start() blocks, so most applications run it in a thread.
thread = Thread(target=client.start, daemon=True)
thread.start()
```

The object and blob callbacks follow the same naming pattern: `add_tuio_object`, `update_tuio_object`, `remove_tuio_object`, `add_tuio_blob`, `update_tuio_blob`, and `remove_tuio_blob`.

Listeners can be removed with `remove_listener(listener)` or all at once with `remove_all_listeners()`.

### Client frame and lifecycle behavior

Received `alive` and `set` messages are buffered and applied atomically when the corresponding `fseq` message completes a frame. This means:

- additions, updates, and removals are visible in the public profile lists only after a valid `fseq`;
- continuing profile instances keep their object identity while their attributes are updated;
- update callbacks are generated only when a received `set` value actually changed;
- removals are derived from the profile's `alive` list;
- listener callbacks are delivered to every registered listener;
- `refresh` marks the end of each accepted frame.

Frame sequence handling follows the TUIO 1.1 reference behavior:

- increasing sequence numbers are accepted;
- repeated sequence numbers are accepted for split or profile-specific bundles;
- older sequence numbers are dropped without state changes, events, or `refresh` callbacks;
- `fseq -1` redundant bundles are processed without advancing the stored frame sequence;
- large backwards jumps are accepted as sequence wraparound.

Malformed or unknown TUIO messages are ignored instead of raising exceptions. Truncated or wrongly typed `set` messages are skipped, while surplus arguments are tolerated.

### Active profiles, sources, and queries

The currently active profiles remain available through the existing public lists:

```python
client.cursors
client.objects
client.blobs
```

TUIO 1.1 `source` messages are decoded so multiple senders can use the same session IDs independently. Received profiles expose additive source metadata:

```python
profile.source_id
profile.source_name
profile.source_address
```

Source strings of the form `name@address` are split into name and address. A bare source name implicitly uses the `localhost` address.

Additive query helpers return shallow copies or matching active profiles:

```python
client.get_tuio_cursors()
client.get_tuio_objects()
client.get_tuio_blobs()

client.get_tuio_cursors(source_id=0)
cursor = client.get_tuio_cursor(session_id, source_id=0)
obj = client.get_tuio_object(session_id)
blob = client.get_tuio_blob(session_id, source_id=1)
```

Passing no `source_id` searches across all sources. Source IDs are assigned in first-seen order, following the reference client. Applications that need reliable source multiplexing should consistently emit explicit `source` messages.

## Compatibility notes

The existing externally facing Python API is preserved:

- `TuioServer`, `TuioClient`, `Cursor`, `Object`, `Blob`, and `TuioListener` keep their existing construction and callback patterns;
- server state remains controlled through the public profile lists and `send_bundle()`;
- client state remains available through the public active-profile lists;
- listener callback names and signatures are unchanged.

The added interfaces are limited to server frame/profile controls, profile source metadata, and client query helpers.

Current limitations:

- TUIO over UDP only; TCP and WebSocket transports are not implemented;
- `TuioClient.start()` is blocking and there is no high-level client stop lifecycle API;
- `refresh` currently receives the historical placeholder value `0` rather than a frame time object;
- local cursor/blob component IDs from the C++ reference client are not implemented;
- periodic server retransmission methods are present but unimplemented.

## Development

Install the runtime and test requirements:

```sh
pip3 install -r pip_requirements.txt
pip3 install -r pip_test_requirements.txt
```

Run the automated offline tests:

```sh
python3 -m pytest unit_test/test_tuio11_server.py unit_test/test_tuio11_client.py -q
```

These tests construct OSC bundles offline and validate TUIO 1.1 wire ordering, type tags, lifecycle behavior, malformed-message handling, frame sequencing, and source multiplexing. `unit_test/tuio_test.py` is a legacy manual/network-dependent test script rather than an automated offline test.

## Contributing

Contributions are welcome. Please open a merge request with your changes.

Project repository: <https://github.com/tweigel-dev/python-tuio>
