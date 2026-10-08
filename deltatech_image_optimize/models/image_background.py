# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64
import logging

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools import SQL

from .ir_attachment import _rembg_available

_logger = logging.getLogger(__name__)

# câmpul original al lui image.mixin și variantele redimensionate din el
IMAGE_FIELD = "image_1920"
IMAGE_VARIANT_FIELDS = ["image_1024", "image_512", "image_256", "image_128"]


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
        date), deci verificarea se face înainte, în wizard. Fără rembg se pot
        decupa doar imaginile pe fundal uniform.
        """
        params = self.env["ir.attachment"]._dt_bg_params()
        if params["method"] == "rembg" and not _rembg_available():
            raise UserError(
                self.env._(
                    "Background removal with the AI model needs the Python library rembg. "
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
            "context": {"dialog_size": "extra-large"},
        }

    # === HELPERS ===#

    def _dt_bg_targets(self):
        """Recordurile ale căror imagini le atinge acțiunea, grupate pe model."""
        return [self]

    def _dt_bg_line_name(self):
        """Numele imaginii în wizard."""
        self.ensure_one()
        return self.display_name

    def _dt_bg_cutout(self, params):
        """Imaginea fără fundal, ca PNG, fără să scrie nimic.

        :return: ``(png, avertisment)``; ``png`` este ``None`` la eșec.
        """
        self.ensure_one()
        try:
            return self.env["ir.attachment"]._dt_image_cutout(base64.b64decode(self[IMAGE_FIELD]), params)
        except Exception as exc:  # noqa: BLE001 - o imagine stricată nu oprește lotul
            _logger.warning("Background removal failed for %s(%s): %s", self._name, self.id, exc)
            return None, str(exc)

    def _dt_bg_apply(self, data):
        """Scrie imaginea fără fundal și o trece pe WebP, cu variante cu tot."""
        self.ensure_one()
        # scrierea prin record regenerează variantele redimensionate din PNG
        self.write({IMAGE_FIELD: base64.b64encode(data), "bg_removal_state": "done"})
        self._dt_bg_compress_attachments()

    def _dt_bg_remove(self, params):
        """Elimină fundalul fără previzualizare (coada procesată de cron)."""
        data, warning = self._dt_bg_cutout(params)
        if not data:
            _logger.info("Background not removed for %s(%s): %s", self._name, self.id, warning)
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

    def _dt_bg_line_name(self):
        self.ensure_one()
        return self.env._("%(product)s — main image", product=self.display_name)


class ProductImage(models.Model):
    _name = "product.image"
    _inherit = ["product.image", "deltatech.image.background.mixin"]

    def _dt_bg_line_name(self):
        # numele imaginii din galerie e de obicei numele produsului: arătăm și poziția,
        # ca o imagine pusă la produsul greșit să se vadă
        self.ensure_one()
        owner = self.product_variant_id or self.product_tmpl_id
        if not owner:
            return self.display_name
        gallery = owner.product_variant_image_ids if self.product_variant_id else owner.product_template_image_ids
        position = gallery.ids.index(self.id) + 1 if self.id in gallery.ids else 0
        name = self.env._("%(product)s — gallery image %(position)s", product=owner.display_name, position=position)
        if self.name and self.name not in owner.display_name:
            name = f"{name} ({self.name})"
        return name

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
