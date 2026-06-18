from collections import defaultdict

from odoo import fields, models

from ..constants import PACKAGING_MATERIAL_TYPES


class AccountMove(models.Model):
    _inherit = "account.move"

    packaging_material_ids = fields.One2many(
        "packaging.invoice.material",
        "invoice_id",
        string="Packaging materials",
    )

    def refresh_packaging_material(self):
        """Recompute packaging quantities from the current invoice lines."""
        for invoice in self.filtered(lambda move: move.move_type != "entry"):
            quantities_by_product = defaultdict(float)
            for line in invoice.invoice_line_ids.filtered("product_id"):
                quantities_by_product[line.product_id] += line.quantity

            quantities_by_material = defaultdict(float)
            for product, quantity in quantities_by_product.items():
                for material in product.product_tmpl_id.packaging_material_ids:
                    quantities_by_material[material.material_type] += quantity * material.qty

            invoice.packaging_material_ids.unlink()
            self.env["packaging.invoice.material"].create(
                [
                    {
                        "invoice_id": invoice.id,
                        "material_type": material_type,
                        "qty": quantity,
                    }
                    for material_type, quantity in quantities_by_material.items()
                ]
            )
        return True

    def action_post(self):
        result = super().action_post()
        for invoice in self.filtered(lambda move: move.move_type != "entry" and not move.packaging_material_ids):
            invoice.refresh_packaging_material()
        return result


class InvoicePackagingMaterial(models.Model):
    _name = "packaging.invoice.material"
    _description = "Packaging material used in an invoice"
    _order = "material_type, id"

    invoice_id = fields.Many2one(
        "account.move",
        required=True,
        ondelete="cascade",
        index=True,
    )
    material_type = fields.Selection(PACKAGING_MATERIAL_TYPES, required=True)
    qty = fields.Float(string="Quantity", required=True)
