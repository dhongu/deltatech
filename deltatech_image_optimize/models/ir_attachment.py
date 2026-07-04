import base64
import gc
import io
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

try:
    from PIL import Image

    # features.check("webp") can report True while the encoder still fails at
    # save time on some builds, so probe with a real encode.
    try:
        _probe = io.BytesIO()
        Image.new("RGBA", (1, 1)).save(_probe, format="WEBP")
        WEBP_OK = True
    except Exception:  # noqa: BLE001
        WEBP_OK = False
except ImportError:  # pragma: no cover
    Image = None
    WEBP_OK = False

DEFAULT_TARGET_FIELDS = "image_1920,image_variant_1920"
DEFAULT_VARIANT_FIELDS = "image_1024,image_512,image_256,image_128"


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
            "batch": int(get("deltatech_image_optimize.batch", 1000)),
            "flush_every": max(1, int(get("deltatech_image_optimize.flush_every", 20))),
            "webp_quality": max(1, min(100, int(get("deltatech_image_optimize.webp_quality", 85)))),
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
    def _dt_image_recompress(raw, quality, max_dim, webp_quality=85):
        """Recompress raw image bytes.

        - photos without transparency -> JPEG (quality tuned, progressive)
        - images with transparency     -> WebP (alpha preserved, ~70% smaller
          than PNG). Note: Odoo cannot resize WebP, so a WebP result must be
          written directly on its attachment, never through the record field
          (that would trigger a broken variant regeneration).
        - animated GIFs                 -> skipped (never flattened)

        :return: tuple ``(data, output_format)`` where output_format is
            ``"JPEG"`` or ``"WEBP"``; or ``(None, None)`` when the image cannot
            be optimized or the result would not be smaller.
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
        resample = getattr(Image, "Resampling", Image).LANCZOS
        if max_dim and max(img.size) > max_dim:
            img.thumbnail((max_dim, max_dim), resample)
        has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
        data = None
        out_format = None
        if has_alpha:
            # WebP preserves alpha and is ~70% smaller than PNG. If the Pillow
            # build cannot encode WebP, fall back to optimized PNG.
            if WEBP_OK:
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
    @api.model
    def _dt_image_optimize_run(self, limit=None):
        """Optimize a batch of original image attachments.

        The smaller image is written back through the owning record
        (``record.write({res_field: ...})``) so Odoo regenerates the resized
        variants (image_1024/512/256/128) from the new, smaller original.

        :return: dict with ``scanned``, ``optimized`` and ``freed`` (bytes).
        """
        if Image is None:
            _logger.warning("Pillow (PIL) is not available; image optimizer skipped.")
            return {"scanned": 0, "optimized": 0, "freed": 0}

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
        # Decoded images and their raw bytes are heavy; flush and drop the ORM
        # cache regularly so memory stays flat over large batches (otherwise a
        # single batch can exhaust the worker/shell memory and get killed).
        # For high-resolution images (e.g. 20 MP) lower flush_every to 2-3.
        flush_every = params["flush_every"]
        for index, att in enumerate(attachments, start=1):
            raw = att.raw
            data, out_format = self._dt_image_recompress(
                raw, params["quality"], params["max_dim"], params["webp_quality"]
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
                        optimized += 1
            if index % flush_every == 0:
                self.env.flush_all()
                self.env.invalidate_all()
                gc.collect()

        _logger.info(
            "Image optimizer: scanned=%s optimized=%s freed=%.1f MB",
            len(attachments),
            optimized,
            freed / 1048576.0,
        )
        return {"scanned": len(attachments), "optimized": optimized, "freed": freed}

    @api.model
    def _dt_image_optimize_variants_run(self, limit=None):
        """Recompress the stored resized variants (image_1024/512/256/128).

        Variants are ``related='image_1920'`` fields, so they must NOT be
        written through the record (that would propagate back and downscale the
        original). Instead we recompress the variant's own attachment in place
        (``att.write({'raw': ...})``): no resize (already sized), just a lower
        quality re-encode. No propagation, original untouched.

        :return: dict with ``scanned``, ``optimized`` and ``freed`` (bytes).
        """
        if Image is None:
            return {"scanned": 0, "optimized": 0, "freed": 0}
        get = self.env["ir.config_parameter"].sudo().get_param
        quality = max(1, min(95, int(get("deltatech_image_optimize.variant_quality", 85))))
        webp_quality = max(1, min(100, int(get("deltatech_image_optimize.webp_quality", 85))))
        min_size = int(get("deltatech_image_optimize.variant_min_size", 20480))
        vfields = [
            name.strip()
            for name in get("deltatech_image_optimize.variant_fields", DEFAULT_VARIANT_FIELDS).split(",")
            if name.strip()
        ]
        limit = limit or int(get("deltatech_image_optimize.batch", 200))
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
        for index, att in enumerate(attachments, start=1):
            raw = att.raw
            # max_dim=0 -> no resize, only a lower quality re-encode.
            data, out_format = self._dt_image_recompress(raw, quality, 0, webp_quality)
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
                optimized += 1
            if index % flush_every == 0:
                self.env.flush_all()
                self.env.invalidate_all()
                gc.collect()

        _logger.info(
            "Image optimizer (variants): scanned=%s optimized=%s freed=%.1f MB",
            len(attachments),
            optimized,
            freed / 1048576.0,
        )
        return {"scanned": len(attachments), "optimized": optimized, "freed": freed}

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
