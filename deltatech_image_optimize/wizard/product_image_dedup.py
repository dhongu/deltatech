# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class ProductImageDedup(models.TransientModel):
    _name = "deltatech.product.image.dedup"
    _description = "Remove Duplicated Product Images"

    state = fields.Selection([("choose", "choose"), ("done", "done")], default="choose", readonly=True)
    checksums = fields.Text(readonly=True)
    group_count = fields.Integer(string="Duplicated Contents", readonly=True)
    removable_count = fields.Integer(string="Images To Remove", readonly=True)
    kept_count = fields.Integer(string="Images Kept", readonly=True)
    preview = fields.Text(string="What Will Be Removed", readonly=True)
    removed_count = fields.Integer(string="Images Removed", readonly=True)

    # === DEFAULTS ===#

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        checksums = self._selected_checksums()
        values["checksums"] = "\n".join(checksums)
        to_remove = self._images_to_remove(checksums)
        values["group_count"] = len(checksums)
        values["removable_count"] = len(to_remove)
        values["kept_count"] = self._kept_count(checksums)
        values["preview"] = self._build_preview(to_remove)
        return values

    def _selected_checksums(self):
        """Checksum-urile din selecția utilizatorului, sau tot catalogul.

        Fără selecție wizardul lucrează pe toate grupurile de duplicate — asta
        e cazul rulării din meniu.
        """
        context = self.env.context
        duplicate_model = "deltatech.product.image.duplicate"
        if context.get("active_model") == duplicate_model and context.get("active_ids"):
            groups = self.env[duplicate_model].browse(context["active_ids"])
        else:
            groups = self.env[duplicate_model].search([("removable_count", ">", 0)])
        return [checksum for checksum in groups.mapped("image_checksum") if checksum]

    # === COMPUTATION ===#

    @api.model
    def _images_to_remove(self, checksums):
        """Imaginile redundante: copiile repetate în cadrul aceluiași produs.

        În fiecare grup (conținut, produs, variantă) rămâne prima imagine după
        ``sequence, id`` — cea pe care website-ul o folosește oricum întâi.
        Aceeași imagine folosită pe produse *diferite* nu e redundantă: fiecare
        produs are nevoie de exemplarul lui.
        """
        if not checksums:
            return self.env["product.image"]
        images = self.env["product.image"].search([("image_checksum", "in", list(checksums))], order="sequence, id")
        seen = set()
        redundant_ids = []
        for image in images:
            if image.video_url:
                # ștergerea ar pierde și videoul, care nu e duplicat
                continue
            key = (image.image_checksum, image.product_tmpl_id.id, image.product_variant_id.id)
            if key in seen:
                redundant_ids.append(image.id)
            else:
                seen.add(key)
        return self.env["product.image"].browse(redundant_ids)

    @api.model
    def _kept_count(self, checksums):
        if not checksums:
            return 0
        images = self.env["product.image"].search([("image_checksum", "in", list(checksums))])
        keys = {(image.image_checksum, image.product_tmpl_id.id, image.product_variant_id.id) for image in images}
        return len(keys)

    @api.model
    def _build_preview(self, images, limit=50):
        lines = []
        for image in images[:limit]:
            product = image.product_variant_id.display_name or image.product_tmpl_id.display_name
            lines.append(f"{product or '-'} — {image.display_name} (#{image.id})")
        if len(images) > limit:
            lines.append(self.env._("... and %s more", len(images) - limit))
        return "\n".join(lines)

    # === ACTIONS ===#

    def action_apply(self):
        self.ensure_one()
        checksums = (self.checksums or "").splitlines()
        to_remove = self._images_to_remove(checksums)
        removed = len(to_remove)
        to_remove.unlink()
        self.write({"state": "done", "removed_count": removed})
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
