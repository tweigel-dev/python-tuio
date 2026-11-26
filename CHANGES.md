# Changes

## 2026-11-26 — TUIO 1.1 compatibility update

This update brings the Python server and client implementations closer to the TUIO 1.1 specification and the behavior of the C++ reference implementation while preserving the existing externally facing Python API. Existing server and client construction, public profile lists, listener callback names, and listener callback signatures remain unchanged.

### Server

- Corrected `send_bundle()` wire output to emit separate profile-specific OSC bundles for `/tuio/2Dcur`, `/tuio/2Dobj`, and `/tuio/2Dblb` instead of one mixed-profile bundle.
- Ordered each profile bundle as optional `source`, `alive`, zero or more `set` messages, and concluding `fseq`.
- Added incrementing nonnegative int32 frame sequence IDs. Profiles belonging to the same `send_bundle()` call share the same frame sequence.
- Implemented the existing `set_source_name()` API.
- Added cursor/object/blob profile enable and query methods.
- Added additive frame-control APIs:
  - `next_fseq()`
  - `send_profile_bundle()`
  - `send_full_messages()`
  - `send_empty_cursor_bundle()`
  - `send_empty_object_bundle()`
  - `send_empty_blob_bundle()`
- `send_full_messages()` and explicit empty bundles use the redundant frame marker `fseq -1` for startup, shutdown, and state resynchronization.

### Client

- Reworked receive-side frame handling so `alive` and `set` messages are buffered and applied atomically when `fseq` completes a frame.
- Fixed listener fanout so every registered listener receives the same add/update/remove events. Previously, event queues were cleared while dispatching to the first listener.
- Removed noisy per-bundle debug printing.
- Replaced the historical `refresh(0)` placeholder with a monotonic session-relative floating-point frame time in seconds. Packets sharing a frame sequence share the same frame time, and recent redundant frames reuse it.
- Preserved object identity for continuing profiles while updating their attributes in place.
- Eliminated spurious update events for unchanged contacts that merely remain present in `alive` lists.
- Added exact field decoding for object, cursor, and blob profiles, including rotation-only blob updates.
- Made malformed and unknown TUIO messages non-fatal:
  - truncated or wrongly typed `set` messages are skipped;
  - surplus `set` arguments are tolerated;
  - unknown and empty commands are ignored;
  - valid frames still complete with a `refresh` callback.
- Implemented TUIO frame sequence behavior:
  - increasing sequence numbers are accepted;
  - repeated sequence numbers are accepted for split/profile-specific bundles;
  - late frames are dropped without state changes, events, or `refresh` callbacks;
  - redundant `fseq -1` bundles are processed without advancing the stored sequence;
  - large backwards jumps are treated as sequence wraparound.
- Implemented source multiplexing:
  - `source` messages are parsed as `name@address`, `name@`, or bare `name`;
  - missing or bare addresses become `localhost`;
  - identical session IDs from distinct sources coexist independently;
  - removals and frame sequence tracking are scoped per source.
- Added additive profile metadata:
  - `source_id`
  - `source_name`
  - `source_address`
- Added additive query helpers:
  - `get_tuio_objects()`, `get_tuio_cursors()`, `get_tuio_blobs()`
  - `get_tuio_object()`, `get_tuio_cursor()`, `get_tuio_blob()`

### Tests and validation

- Added offline OSC wire-format and dispatcher tests covering bundle ordering, type tags, lifecycle behavior, malformed input, frame sequencing, split bundles, redundant frames, source multiplexing, and legacy mixed-profile bundles.
- Validated Python server/client interoperability for cursor, object, and blob profiles, including source metadata and shutdown state clearing.
- Exercised the client against the reference `TuioAudit` generator using normal scenarios (`mixed`, `static`, `churn`, `empty`) and malformed scenarios (`noalive`, `setonly`, `nofseq`, `shortset`, `longset`, `badtype`, `deadset`) without exceptions or per-frame debug output.

### Remaining limitations

- TUIO is supported over UDP only; TCP and WebSocket transports are not implemented.
- `TuioClient.start()` remains blocking and no high-level client stop lifecycle API was added.
- Frame times are monotonic session-relative seconds rather than wall-clock timestamps or a dedicated time object.
- Local cursor/blob component IDs from the C++ reference client are not implemented.
- Periodic server retransmission methods remain unimplemented.
- The server does not automatically split very large frames across multiple UDP packets.
