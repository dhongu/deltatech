# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64
import io
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import SQL

from .ir_attachment import Image, _webp_available

_logger = logging.getLogger(__name__)

# câmpul original al lui image.mixin și variantele redimensionate din el
IMAGE_FIELD = "image_1920"
IMAGE_VARIANT_FIELDS = ["image_1024", "image_512", "image_256", "image_128"]

# o sesiune rembg încarcă modelul ONNX (~180 MB pentru isnet); o păstrăm per proces
_REMBG_SESSIONS = {}


def _rembg_available():
    try:
        import rembg  # noqa: F401
    except ImportError:
        return False
    return True


def _rembg_cutout(img, model_name):
    """Decupează produsul din ``img`` și întoarce o imagine RGBA.

    rembg e o dependență opțională, importată doar aici: e grea (onnxruntime,
    modelul se descarcă la prima folosire), iar modulul nu trebuie să ceară
    instalarea ei la clienții care folosesc doar recomprimarea.
    """
    from rembg import new_session, remove

    session = _REMBG_SESSIONS.get(model_name)
    if session is None:
        session = _REMBG_SESSIONS[model_name] = new_session(model_name)
    return remove(img, session=session, post_process_mask=True)


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.model
    def _dt_bg_params(self):
        get = self.env["ir.config_parameter"].sudo().get_param
        return {
            "model": get("deltatech_image_optimize.bg_model", "isnet-general-use"),
            "crop": get("deltatech_image_optimize.bg_crop", "0") in ("1", "True", "true"),
            "margin": max(0, min(40, int(get("deltatech_image_optimize.bg_margin", 5)))),
            "color": (get("deltatech_image_optimize.bg_color", "") or "").strip(),
            "sync_limit": int(get("deltatech_image_optimize.bg_sync_limit", 5)),
            "batch": max(1, int(get("deltatech_image_optimize.bg_batch", 20))),
        }

    @staticmethod
    def _dt_image_remove_background(raw, model_name, crop=False, margin=5, color=""):
        """Elimină fundalul din octeții unei imagini.

        - ``crop``: încadrează produsul într-un pătrat, cu ``margin`` procente
          margine de jur împrejur; altfel păstrează pânza originală.
        - ``color``: fundal plin (de ex. ``#FFFFFF``) în locul transparenței.

        :return: octeții unui PNG (RGBA, sau RGB când e dată o culoare), sau
            ``None`` când modelul nu a găsit niciun obiect în imagine.
        """
        if not raw or Image is None:
            return None
        # imaginile de produs sunt deseori WebP, iar Odoo nu înregistrează pluginul
        _webp_available()
        img = Image.open(io.BytesIO(raw))
        img.load()
        from PIL import ImageOps

        img = ImageOps.exif_transpose(img).convert("RGB")
        out = _rembg_cutout(img, model_name).convert("RGBA")
        bbox = out.getchannel("A").getbbox()
        if not bbox:
            return None
        if crop:
            out = out.crop(bbox)
            side = int(max(out.size) * (1 + 2 * margin / 100.0))
            canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
            canvas.paste(out, ((side - out.width) // 2, (side - out.height) // 2), out)
            out = canvas
        if color:
            flat = Image.new("RGBA", out.size, color)
            flat.alpha_composite(out)
            out = flat.convert("RGB")
        buf = io.BytesIO()
        out.save(buf, format="PNG")
        return buf.getvalue()

    @api.model
    def _dt_bg_remove_cron(self):
        """Procesează imaginile puse în coadă de acțiunea „Elimină fundalul”."""
        params = self._dt_bg_params()
        remaining = 0
        for model_name in ("product.template", "product.image"):
            model = self.env[model_name].sudo()
            records = model.search([("bg_removal_state", "=", "pending")], limit=params["batch"])
            for record in records:
                record._dt_bg_remove(params)
                # un lot întrerupt de limita de timp a workerului nu reia ce s-a făcut deja
                self.env.cr.commit()  # pylint: disable=invalid-commit
            remaining += model.search_count([("bg_removal_state", "=", "pending")])
        if remaining:
            self.env.ref("deltatech_image_optimize.ir_cron_dt_image_remove_background")._trigger()


class ImageBackgroundMixin(models.AbstractModel):
    _name = "deltatech.image.background.mixin"
    _description = "Product Image Background Removal"

    bg_removal_state = fields.Selection(
        [("pending", "Pending"), ("done", "Removed"), ("error", "Failed")],
        string="Background Removal",
        copy=False,
        index=True,
    )

    # === ACTIONS ===#

    def action_dt_remove_background(self):
        """Deschide wizard-ul: previzualizare pentru puține imagini, coadă pentru multe.

        Originalul nu se păstrează după aplicare (ar dubla imaginile în baza de
        date), deci verificarea se face înainte, în wizard.
        """
        if not _rembg_available():
            raise UserError(
                self.env._(
                    "Background removal needs the Python library rembg. "
                    'Add "rembg[cpu]" to the requirements.txt of the deployment and rebuild.'
                )
            )
        targets = [records.filtered(IMAGE_FIELD) for records in self._dt_bg_targets()]
        wizard = self.env["deltatech.image.background.wizard"]._dt_create_for(targets)
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Remove Image Background"),
            "res_model": wizard._name,
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    # === HELPERS ===#

    def _dt_bg_targets(self):
        """Recordurile ale căror imagini le atinge acțiunea, grupate pe model."""
        return [self]

    def _dt_bg_cutout(self, params):
        """Imaginea fără fundal, ca PNG, fără să scrie nimic; ``None`` la eșec."""
        self.ensure_one()
        try:
            return self.env["ir.attachment"]._dt_image_remove_background(
                base64.b64decode(self[IMAGE_FIELD]), params["model"], params["crop"], params["margin"], params["color"]
            )
        except Exception as exc:  # noqa: BLE001 - o imagine stricată nu oprește lotul
            _logger.warning("Background removal failed for %s(%s): %s", self._name, self.id, exc)
            return None

    def _dt_bg_apply(self, data):
        """Scrie imaginea fără fundal și o trece pe WebP, cu variante cu tot."""
        self.ensure_one()
        # scrierea prin record regenerează variantele redimensionate din PNG
        self.write({IMAGE_FIELD: base64.b64encode(data), "bg_removal_state": "done"})
        self._dt_bg_compress_attachments()

    def _dt_bg_remove(self, params):
        """Elimină fundalul fără previzualizare (coada procesată de cron)."""
        data = self._dt_bg_cutout(params)
        if not data:
            self.bg_removal_state = "error"
            return False
        self._dt_bg_apply(data)
        return True

    def _dt_bg_compress_attachments(self):
        """Trece imaginea și variantele ei pe WebP, direct pe atașamente.

        Odoo nu redimensionează WebP, deci WebP-ul nu poate fi scris prin câmp
        (ar ieși toate variantele la mărimea originală). Scriem întâi PNG-ul prin
        record, ca Odoo să genereze variantele, apoi recodăm fiecare atașament
        pe loc — același drum ca optimizatorul pentru imaginile transparente.
        """
        self.env.flush_all()
        attachment_model = self.env["ir.attachment"].sudo()
        params = attachment_model._dt_image_optimize_params()
        attachments = attachment_model.search(
            [
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
                ("res_field", "in", [IMAGE_FIELD, *IMAGE_VARIANT_FIELDS]),
            ]
        )
        now = fields.Datetime.now()
        for att in attachments:
            data, out_format = attachment_model._dt_image_recompress(
                att.raw, params["quality"], 0, params["webp_quality"], False
            )
            vals = {"deltatech_image_optimized": now}
            if data:
                vals["raw"] = data
                vals["mimetype"] = {"WEBP": "image/webp", "PNG": "image/png"}.get(out_format, "image/jpeg")
            att.write(vals)


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["product.template", "deltatech.image.background.mixin"]

    def _dt_bg_targets(self):
        # pe produs, acțiunea curăță și imaginile suplimentare din galerie
        return [self, self.product_template_image_ids]


class ProductImage(models.Model):
    _name = "product.image"
    _inherit = ["product.image", "deltatech.image.background.mixin"]

    def _dt_bg_compress_attachments(self):
        res = super()._dt_bg_compress_attachments()
        # recodarea pe loc schimbă checksum-ul atașamentului, după care se face deduplicarea
        self.env.flush_all()
        checksums = self._dedup_attachment_checksums()
        self.env.cr.execute(
            SQL(
                "UPDATE product_image SET image_checksum = %s WHERE id = %s",
                checksums.get(self.id),
                self.id,
            )
        )
        self.invalidate_recordset(["image_checksum"])
        return res
