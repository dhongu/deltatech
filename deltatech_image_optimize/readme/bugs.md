# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## IMAGE-001 — P1: Animated PNG and WebP images are flattened during optimization

- **Status:** Open.
- **Location:** models/ir_attachment.py, _dt_image_recompress().
- **Trigger:** An eligible original or resized attachment contains an animated PNG or WebP and recompression produces a smaller image.
- **Actual behavior:** Animation is skipped only when the format equals GIF. For other multi-frame formats, the method loads and converts the first frame, then saves a single-frame JPEG/PNG/WebP. The batch runner overwrites the attachment with this result.
- **Evidence:** Executed the actual recompression method extracted by AST with Pillow on a generated four-frame APNG. Input: PNG, four frames, 572292 bytes. Output: JPEG, one frame, 42974 bytes. No database attachment modified. The cron explicitly commits and runs filestore garbage collection after replacing attachments.
- **Impact:** Animated product content becomes a static image; the source attachment is replaced and its old file may subsequently be reclaimed.
- **Suggested fix:** Detect is_animated or n_frames greater than one regardless of format and skip these files, or use an animation-preserving encoder that retains timing and loop metadata.
- **Validation needed:** Animated GIF/APNG/WebP and static PNG/WebP/JPEG, both original and variant runners; verify frame count, timing and loop preservation.

## Review limitations

All eligible Python and XML source files manually reviewed, including checksum backfill, SQL duplicate view, deduplication wizard, ACLs, image processing, configuration and cron. The isolated Pillow reproduction above is not an Odoo integration test. No optimizer cron, deletion wizard, database writes or filestore cleanup executed.
