# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64
import io
import json
import logging

from odoo import fields, models
from odoo.exceptions import UserError

from . import watermark
from .image_background import IMAGE_FIELD
from .ir_attachment import _webp_available

_logger = logging.getLogger(__name__)


class ImageWatermarkProfile(models.Model):
    """Watermark-ul învățat dintr-o selecție de imagini, folosit apoi la eliminare."""

    _name = "deltatech.image.watermark.profile"
    _description = "Learned Image Watermark"
    _order = "id desc"

    name = fields.Char(required=True)
    kind = fields.Selection(
        [("alpha", "Transparency trace")],
        required=True,
        default="alpha",
        help="Transparency trace: the watermark lowered the transparency of the image where it was "
        "blended, so its exact mask is still in the image.",
    )
    model_data = fields.Text(readonly=True, help="The learned blend, as JSON.")
    image_count = fields.Integer(string="Learned From", readonly=True, help="Images the watermark was learned from.")
    preview = fields.Image(string="Watermark", max_width=1024, max_height=1024, readonly=True)

    def _dt_model(self):
        self.ensure_one()
        return json.loads(self.model_data)

    def _dt_clean(self, raw):
        """Imaginea fără watermark, ca PNG opac, fără să scrie nimic.

        :return: ``(png, avertisment)``; ``png`` este ``None`` când imaginea nu are watermark-ul.
        """
        self.ensure_one()
        _webp_available()
        img = watermark.load_rgba(raw)
        if not watermark.has_alpha_trace(img):
            return None, self.env._("No watermark trace was found in this image.")
        out = watermark.remove_alpha_trace(img, self._dt_model())
        buf = io.BytesIO()
        out.save(buf, format="PNG")
        return buf.getvalue(), ""

    def _dt_learn(self, records):
        """Învață watermark-ul din imaginile recordurilor și creează profilul."""
        if not watermark.numpy_available():
            raise UserError(
                self.env._(
                    "Watermark removal needs the Python library numpy. "
                    'Add "numpy" to the requirements.txt of the deployment and rebuild.'
                )
            )
        _webp_available()
        limit = self.env["ir.attachment"]._dt_wm_params()["learn_limit"]
        images = []
        for record in records:
            img = watermark.load_rgba(base64.b64decode(record[IMAGE_FIELD]))
            if watermark.has_alpha_trace(img):
                images.append(img)
                if len(images) >= limit:
                    break
        if not images:
            raise UserError(
                self.env._(
                    "No watermark trace was found in the selected images. For now, only a watermark that "
                    "left a trace in the image transparency can be removed."
                )
            )
        model = watermark.learn_alpha_trace(images)
        if not model:
            raise UserError(
                self.env._(
                    "The watermark could not be learned from these images. Select more products, including "
                    "some with darker areas under the watermark."
                )
            )
        buf = io.BytesIO()
        watermark.trace_preview(images[0]).save(buf, format="PNG")
        return self.create(
            {
                "name": self.env._("Watermark of %(date)s", date=fields.Date.to_string(fields.Date.today())),
                "model_data": json.dumps(model),
                "image_count": len(images),
                "preview": base64.b64encode(buf.getvalue()),
            }
        )


class ImageBackgroundMixin(models.AbstractModel):
    _inherit = "deltatech.image.background.mixin"

    wm_removal_state = fields.Selection(
        [("pending", "Pending"), ("done", "Removed"), ("error", "Failed")],
        string="Watermark Removal",
        copy=False,
        index=True,
    )
    wm_profile_id = fields.Many2one("deltatech.image.watermark.profile", string="Watermark", copy=False)

    # === ACTIONS ===#

    def action_dt_remove_watermark(self):
        """Învață watermark-ul din selecție și deschide asistentul de verificare."""
        targets = [records.filtered(IMAGE_FIELD) for records in self._dt_bg_targets()]
        wizard = self.env["deltatech.image.watermark.wizard"]._dt_create_for(targets)
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Remove Watermark"),
            "res_model": wizard._name,
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
            "context": {"dialog_size": "extra-large"},
        }

    # === HELPERS ===#

    def _dt_wm_clean(self, profile):
        """Imaginea fără watermark, ca PNG; ``(None, motiv)`` la eșec."""
        self.ensure_one()
        try:
            return profile._dt_clean(base64.b64decode(self[IMAGE_FIELD]))
        except Exception as exc:  # noqa: BLE001 - o imagine stricată nu oprește lotul
            _logger.warning("Watermark removal failed for %s(%s): %s", self._name, self.id, exc)
            return None, str(exc)

    def _dt_wm_apply(self, data):
        """Scrie imaginea fără watermark, cu variante cu tot."""
        self.ensure_one()
        self.write({IMAGE_FIELD: base64.b64encode(data), "wm_removal_state": "done"})
        self._dt_bg_compress_attachments()

    def _dt_wm_remove(self):
        """Elimină watermark-ul fără previzualizare (coada procesată de cron)."""
        self.ensure_one()
        data, warning = self._dt_wm_clean(self.wm_profile_id)
        if not data:
            _logger.info("Watermark not removed for %s(%s): %s", self._name, self.id, warning)
            self.wm_removal_state = "error"
            return False
        self._dt_wm_apply(data)
        return True
