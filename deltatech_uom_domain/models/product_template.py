# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["product.template", "deltatech.uom.domain.mixin"]

    purchase_uom_id = fields.Many2one(
        "uom.uom",
        string="Default Purchase Unit",
        domain="[('id', 'in', purchase_allowed_uom_ids)]",
        help="Unit proposed on purchase order lines when the vendor has no valid pricelist line "
        "for the product (missing, expired or for another vendor).",
    )
    purchase_allowed_uom_ids = fields.Many2many("uom.uom", compute="_compute_purchase_allowed_uom_ids")

    @api.depends("uom_id", "uom_ids")
    def _compute_purchase_allowed_uom_ids(self):
        """Doar unitatile convertibile la UM produsului - acelasi arbore de referinta."""
        for record in self:
            record.purchase_allowed_uom_ids = record.uom_id | record.uom_ids
        self._extend_allowed_uom_ids("purchase_allowed_uom_ids")

    def _uom_domain_product_uom(self):
        self.ensure_one()
        return self.uom_id

    @api.constrains("uom_id", "purchase_uom_id")
    def _check_purchase_uom_id(self):
        """In 19.0 `_compute_quantity()` nu mai verifica compatibilitatea: domeniul din
        formular nu ajunge, o scriere prin import sau RPC ar trece o unitate din alt arbore."""
        for record in self:
            if (
                record.purchase_uom_id
                and record.uom_id
                and not record.purchase_uom_id._has_common_reference(record.uom_id)
            ):
                raise ValidationError(
                    self.env._(
                        "The default purchase unit %(purchase_uom)s of %(product)s "
                        "cannot be converted to its unit %(uom)s.",
                        purchase_uom=record.purchase_uom_id.name,
                        product=record.display_name,
                        uom=record.uom_id.name,
                    )
                )
