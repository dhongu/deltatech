import base64
import gc
import io
import logging

from odoo import api, fields, models
from odoo.tools import SQL

_logger = logging.getLogger(__name__)

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

DEFAULT_TARGET_FIELDS = "image_1920,image_variant_1920"
DEFAULT_VARIANT_FIELDS = "image_1024,image_512,image_256,image_128"

# Resolved on first use by _webp_available(), never at import time: see below.
_WEBP_OK = None


def _ensure_pillow_webp():
    """Register Pillow's WebP plugin, which Odoo leaves out.

    ``odoo/tools/image.py`` runs ``Image.preinit()`` and then sets
    ``Image._initialized = 2``. preinit registers only BMP/GIF/JPEG/PPM/PNG, and
    the flag tells Pillow that ``init()`` already ran, so ``save()`` never loads
    the remaining plugins: ``save(format="WEBP")`` raises ``KeyError: 'WEBP'``
    even on a Pillow built with libwebp (``features.check("webp")`` is True).

    Importing the plugin registers the format directly, which is what actually
    fixes it -- ``Image.init()`` alone returns early on ``_initialized >= 2``.
    Same approach as ``deltatech_website_watermark``.
    """
    if Image is None:  # pragma: no cover
        return
    try:
        from PIL import WebPImagePlugin as _webp_plugin  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        _logger.warning("Pillow WebP plugin import failed (WEBP unavailable): %s", exc)
    try:
        Image.preinit()
        Image.init()
    except Exception as exc:  # noqa: BLE001 - init is best effort
        _logger.debug("Pillow Image.init() raised: %s", exc)


def _webp_available():
    """Whether this process can encode WebP, resolved lazily and cached.

    Deliberately not a module-level constant. The answer depends on whether the
    WebP plugin is registered, which in turn depends on module import order --
    so a constant computed at import time made the module behave differently
    from one database to another (WebP where a module registering the plugin
    happened to be imported first, PNG everywhere else), silently.

    ``features.check("webp")`` is not enough on its own: it can report True
    while ``save()`` still fails, so probe with a real encode.
    """
    global _WEBP_OK
    if _WEBP_OK is None:
        _ensure_pillow_webp()
        try:
            probe = io.BytesIO()
            Image.new("RGBA", (1, 1)).save(probe, format="WEBP")
            _WEBP_OK = True
        except Exception as exc:  # noqa: BLE001
            _WEBP_OK = False
            _logger.info(
                "WebP encoding unavailable (%s); transparent images keep optimized PNG.",
                exc,
            )
    return _WEBP_OK


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    deltatech_image_optimized = fields.Datetime(
        string="Image Optimized On",
        copy=False,
        index=True,
        help="Set once the image optimizer has recompressed this image "
        "attachment. Prevents reprocessing on the next run. Updated images "
        "get a fresh attachment (empty flag) and are picked up automatically.",
    )

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    @api.model
    def _dt_image_optimize_params(self):
        """Read the optimizer configuration from ir.config_parameter."""
        get = self.env["ir.config_parameter"].sudo().get_param
        return {
            "quality": max(1, min(95, int(get("deltatech_image_optimize.quality", 85)))),
            "max_dim": int(get("deltatech_image_optimize.max_dim", 1920)),
            "min_size": int(get("deltatech_image_optimize.min_size", 102400)),
            "batch": int(get("deltatech_image_optimize.batch", 50)),
            "flush_every": max(1, int(get("deltatech_image_optimize.flush_every", 20))),
            "webp_quality": max(1, min(100, int(get("deltatech_image_optimize.webp_quality", 85)))),
            "force_jpeg": get("deltatech_image_optimize.force_jpeg", "0") in ("1", "True", "true"),
            "fields": [
                name.strip()
                for name in get("deltatech_image_optimize.target_fields", DEFAULT_TARGET_FIELDS).split(",")
                if name.strip()
            ],
        }

    # ------------------------------------------------------------------
    # Core recompression
    # ------------------------------------------------------------------
    @staticmethod
    def _dt_image_recompress(raw, quality, max_dim, webp_quality=85, force_jpeg=False):
        """Recompress raw image bytes.

        The transparency is decided by the *actual* alpha content, not just the
        mode (many product images are RGBA/palette but fully opaque):

        - effectively opaque (or no alpha) -> JPEG (quality tuned, progressive)
        - genuinely transparent            -> WebP (alpha preserved, ~70%
          smaller than PNG). Odoo cannot resize WebP, so a WebP result must be
          written directly on its attachment, never through the record field.
          If WebP encoding is unavailable, keep an optimized PNG (never flatten
          real transparency to a solid background).
        - animated GIFs                    -> skipped (never flattened)

        :return: tuple ``(data, output_format)`` where output_format is
            ``"JPEG"``, ``"WEBP"`` or ``"PNG"``; or ``(None, None)`` when the
            image cannot be optimized or the result would not be smaller.
        """
        if not raw or Image is None:
            return None, None
        try:
            img = Image.open(io.BytesIO(raw))
            img.load()
        except Exception:  # noqa: BLE001 - any unreadable image is skipped
            return None, None
        fmt = (img.format or "").upper()
        if fmt == "GIF" and getattr(img, "is_animated", False):
            return None, None
        # Normalize palette (incl. palette transparency) to a real RGBA/RGB
        # image so alpha can be inspected reliably.
        if img.mode == "P":
            img = img.convert("RGBA" if "transparency" in img.info else "RGB")
        resample = getattr(Image, "Resampling", Image).LANCZOS
        if max_dim and max(img.size) > max_dim:
            img.thumbnail((max_dim, max_dim), resample)
        # Detect *real* transparency: an alpha channel that is actually used.
        # With force_jpeg, alpha is ignored entirely (images that are not truly
        # transparent, e.g. a solid colored background) -> always JPEG.
        real_alpha = False
        if not force_jpeg and img.mode in ("RGBA", "LA"):
            try:
                real_alpha = img.getchannel("A").getextrema()[0] < 250
            except (ValueError, IndexError):  # pragma: no cover
                real_alpha = True
        data = None
        out_format = None
        if real_alpha:
            # Preserve transparency: WebP if available, otherwise optimized PNG
            # (never JPEG, which would fill transparent areas).
            if _webp_available():
                try:
                    buf = io.BytesIO()
                    img.convert("RGBA").save(buf, format="WEBP", quality=webp_quality, method=6)
                    data, out_format = buf.getvalue(), "WEBP"
                except Exception:  # noqa: BLE001 - WebP encoder unavailable at runtime
                    data = None
            if data is None:
                buf = io.BytesIO()
                img.convert("RGBA").save(buf, format="PNG", optimize=True)
                data, out_format = buf.getvalue(), "PNG"
        else:
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
            data, out_format = buf.getvalue(), "JPEG"
        if len(data) < len(raw):
            return data, out_format
        return None, None

    # ------------------------------------------------------------------
    # Batch runner
    # ------------------------------------------------------------------
    def _dt_image_shared_file(self):
        """Whether this attachment's filestore file is shared with others.

        Odoo keeps a single file per checksum, so several attachments with the
        same content point at the same ``store_fname``. Recompressing one of
        them frees nothing on disk while the others still reference the old
        file -- which is why the per-attachment byte difference overstates the
        real saving, badly, on catalogs that reuse the same picture (measured
        on a real deployment: 29 GB counted, ~4 GB actually reclaimed, because
        815k image attachments lived in 508k files).

        ``store_fname`` is indexed (``checksum`` is not), and it is derived from
        the checksum, so it answers the same question and is cheap to ask.

        Queried in SQL on purpose: ``search`` on ``ir.attachment`` silently adds
        ``res_field = False`` when the domain does not mention that field, which
        hides exactly the image attachments this module works on -- the count
        then comes back as 0 and every file looks unshared.
        """
        self.ensure_one()
        if not self.store_fname:  # stored in DB, not in the filestore
            return False
        self.env.cr.execute(SQL("SELECT count(*) FROM ir_attachment WHERE store_fname = %s", self.store_fname))
        return self.env.cr.fetchone()[0] > 1

    @api.model
    def _dt_image_optimize_run(self, limit=None):
        """Optimize a batch of original image attachments.

        The smaller image is written back through the owning record
        (``record.write({res_field: ...})``) so Odoo regenerates the resized
        variants (image_1024/512/256/128) from the new, smaller original.

        :return: dict with ``scanned``, ``optimized``, ``freed`` and
            ``freed_disk`` (bytes). ``freed`` sums the per-attachment size
            difference; ``freed_disk`` counts only attachments whose filestore
            file was not shared with another attachment, so it is the figure
            that matches what the disk actually gives back.
        """
        if Image is None:
            _logger.warning("Pillow (PIL) is not available; image optimizer skipped.")
            return {"scanned": 0, "optimized": 0, "freed": 0, "freed_disk": 0}

        params = self._dt_image_optimize_params()
        limit = limit or params["batch"]
        domain = [
            ("res_field", "in", params["fields"]),
            ("deltatech_image_optimized", "=", False),
        ]
        if params["min_size"]:
            domain.append(("file_size", ">", params["min_size"]))

        # sudo() bypasses the record rule that hides field-stored attachments.
        attachments = self.sudo().search(domain, order="file_size desc", limit=limit)

        now = fields.Datetime.now()
        optimized = 0
        freed = 0
        freed_disk = 0
        # Decoded images and their raw bytes are heavy; flush and drop the ORM
        # cache regularly so memory stays flat over large batches (otherwise a
        # single batch can exhaust the worker/shell memory and get killed).
        # For high-resolution images (e.g. 20 MP) lower flush_every to 2-3.
        flush_every = params["flush_every"]
        for index, att in enumerate(attachments, start=1):
            raw = att.raw
            # Ask before writing: the write replaces store_fname, so afterwards
            # there is no way to tell whether the old file was shared.
            shared = att._dt_image_shared_file()
            data, out_format = self._dt_image_recompress(
                raw, params["quality"], params["max_dim"], params["webp_quality"], params["force_jpeg"]
            )
            if not data:
                att.deltatech_image_optimized = now
            elif out_format == "WEBP":
                # Alpha image -> WebP. Odoo cannot resize WebP, so we must NOT
                # write through the record (that would regenerate full-size
                # variants). Write the attachment in place; the variants are
                # handled separately by _dt_image_optimize_variants_run.
                try:
                    att.write({"raw": data, "mimetype": "image/webp", "deltatech_image_optimized": now})
                except Exception as exc:  # noqa: BLE001
                    _logger.warning("Image optimize (webp) failed for att %s: %s", att.id, exc)
                    att.deltatech_image_optimized = now
                else:
                    freed += len(raw) - len(data)
                    if not shared:
                        freed_disk += len(raw) - len(data)
                    optimized += 1
            else:
                record = self.env[att.res_model].sudo().browse(att.res_id)
                if not record.exists() or att.res_field not in record._fields:
                    att.deltatech_image_optimized = now
                else:
                    try:
                        record.write({att.res_field: base64.b64encode(data)})
                    except Exception as exc:  # noqa: BLE001
                        _logger.warning(
                            "Image optimize failed for %s(%s).%s: %s",
                            att.res_model,
                            att.res_id,
                            att.res_field,
                            exc,
                        )
                        att.deltatech_image_optimized = now
                    else:
                        # Writing the image field recreates the attachment:
                        # flag the new one so it is not reprocessed next run.
                        new_att = self.sudo().search(
                            [
                                ("res_model", "=", att.res_model),
                                ("res_id", "=", att.res_id),
                                ("res_field", "=", att.res_field),
                            ],
                            limit=1,
                        )
                        if new_att:
                            new_att.deltatech_image_optimized = now
                        freed += len(raw) - len(data)
                        if not shared:
                            freed_disk += len(raw) - len(data)
                        optimized += 1
            if index % flush_every == 0:
                self.env.flush_all()
                self.env.invalidate_all()
                gc.collect()

        _logger.info(
            "Image optimizer: scanned=%s optimized=%s freed=%.1f MB (on disk: %.1f MB)",
            len(attachments),
            optimized,
            freed / 1048576.0,
            freed_disk / 1048576.0,
        )
        return {
            "scanned": len(attachments),
            "optimized": optimized,
            "freed": freed,
            "freed_disk": freed_disk,
        }

    @api.model
    def _dt_image_optimize_variants_run(self, limit=None):
        """Recompress the stored resized variants (image_1024/512/256/128).

        Variants are ``related='image_1920'`` fields, so they must NOT be
        written through the record (that would propagate back and downscale the
        original). Instead we recompress the variant's own attachment in place
        (``att.write({'raw': ...})``): no resize (already sized), just a lower
        quality re-encode. No propagation, original untouched.

        :return: dict with ``scanned``, ``optimized``, ``freed`` and
            ``freed_disk`` (bytes). ``freed`` sums the per-attachment size
            difference; ``freed_disk`` counts only attachments whose filestore
            file was not shared with another attachment, so it is the figure
            that matches what the disk actually gives back.
        """
        if Image is None:
            return {"scanned": 0, "optimized": 0, "freed": 0, "freed_disk": 0}
        get = self.env["ir.config_parameter"].sudo().get_param
        quality = max(1, min(95, int(get("deltatech_image_optimize.variant_quality", 85))))
        webp_quality = max(1, min(100, int(get("deltatech_image_optimize.webp_quality", 85))))
        force_jpeg = get("deltatech_image_optimize.force_jpeg", "0") in ("1", "True", "true")
        min_size = int(get("deltatech_image_optimize.variant_min_size", 20480))
        vfields = [
            name.strip()
            for name in get("deltatech_image_optimize.variant_fields", DEFAULT_VARIANT_FIELDS).split(",")
            if name.strip()
        ]
        limit = limit or int(get("deltatech_image_optimize.batch", 50))
        flush_every = max(1, int(get("deltatech_image_optimize.flush_every", 20)))
        domain = [
            ("res_field", "in", vfields),
            ("deltatech_image_optimized", "=", False),
        ]
        if min_size:
            domain.append(("file_size", ">", min_size))
        attachments = self.sudo().search(domain, order="file_size desc", limit=limit)

        now = fields.Datetime.now()
        optimized = 0
        freed = 0
        freed_disk = 0
        for index, att in enumerate(attachments, start=1):
            raw = att.raw
            # Ask before writing: the write replaces store_fname.
            shared = att._dt_image_shared_file()
            # max_dim=0 -> no resize, only a lower quality re-encode.
            data, out_format = self._dt_image_recompress(raw, quality, 0, webp_quality, force_jpeg)
            vals = {"deltatech_image_optimized": now}
            if data:
                vals["raw"] = data
                if out_format == "WEBP":
                    vals["mimetype"] = "image/webp"
            try:
                att.write(vals)
            except Exception as exc:  # noqa: BLE001
                _logger.warning("Variant optimize failed for att %s: %s", att.id, exc)
                continue
            if data:
                freed += len(raw) - len(data)
                if not shared:
                    freed_disk += len(raw) - len(data)
                optimized += 1
            if index % flush_every == 0:
                self.env.flush_all()
                self.env.invalidate_all()
                gc.collect()

        _logger.info(
            "Image optimizer (variants): scanned=%s optimized=%s freed=%.1f MB (on disk: %.1f MB)",
            len(attachments),
            optimized,
            freed / 1048576.0,
            freed_disk / 1048576.0,
        )
        return {
            "scanned": len(attachments),
            "optimized": optimized,
            "freed": freed,
            "freed_disk": freed_disk,
        }

    @api.model
    def _dt_image_optimize_cron(self):
        """Entry point for the scheduled action: originals then variants,
        followed by a filestore GC so the freed space is actually reclaimed
        (the cron is the single writer here, so it can grab the GC lock)."""
        self._dt_image_optimize_run()
        self._dt_image_optimize_variants_run()
        # the GC needs the optimized attachments committed before it can
        # safely unlink the old filestore entries
        self.env.cr.commit()  # pylint: disable=invalid-commit
        self._gc_file_store()
