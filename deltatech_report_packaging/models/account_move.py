from collections import defaultdict

from odoo import api, fields, models

from ..constants import PACKAGING_MATERIAL_TYPES


class AccountMove(models.Model):
    _inherit = "account.move"

    packaging_material_ids = fields.One2many(
        "packaging.invoice.material",
        "invoice_id",
        string="Packaging materials",
    )
    packaging_material_auto = fields.Boolean(
        string="Auto-update packaging materials",
        default=True,
        help="Keep the packaging material quantities computed from the invoice lines and "
        "refreshed when the invoice is posted. Unset it to keep the quantities entered by "
        "hand: editing or deleting a quantity unsets it automatically, and the Refresh "
        "button computes them again and sets it back.",
    )

    def _packaging_material_direction(self):
        """Which product quantity applies: the purchase one or the sale one."""
        self.ensure_one()
        return "purchase" if self.move_type in ("in_invoice", "in_refund", "in_receipt") else "sale"

    def refresh_packaging_material(self):
        """Recompute packaging quantities from the current invoice lines."""
        for invoice in self.filtered(lambda move: move.move_type != "entry"):
            direction = invoice._packaging_material_direction()
            quantities_by_product = defaultdict(float)
            for line in invoice.invoice_line_ids.filtered("product_id"):
                quantities_by_product[line.product_id] += line.quantity

            quantities_by_material = defaultdict(float)
            for product, quantity in quantities_by_product.items():
                for material in product.product_tmpl_id.packaging_material_ids:
                    quantities_by_material[material.material_type] += quantity * material._get_qty(direction)

            # `packaging_material_sync` tells the lines that this write comes from the
            # computation itself, so that it is not mistaken for a manual edit
            # (which would unset `packaging_material_auto`, ticket #9413).
            invoice.packaging_material_ids.with_context(packaging_material_sync=True).unlink()
            self.env["packaging.invoice.material"].with_context(packaging_material_sync=True).create(
                [
                    {
                        "invoice_id": invoice.id,
                        "material_type": material_type,
                        "qty": quantity,
                    }
                    for material_type, quantity in quantities_by_material.items()
                    # a material only packed in the other direction has nothing to report
                    if quantity
                ]
            )
            # an explicit refresh takes the invoice back under automatic update
            if not invoice.packaging_material_auto:
                invoice.packaging_material_auto = True
        return True

    def _packaging_material_mark_manual_on_invoice(self):
        """Unset the automatic update, the packaging quantities being set by hand."""
        if self.env.context.get("packaging_material_sync"):
            return
        # a line can be unlinked together with its invoice, which is then already gone
        manual = self.exists().filtered("packaging_material_auto")
        if manual:
            manual.packaging_material_auto = False

    def action_post(self):
        result = super().action_post()
        auto = self.filtered(lambda move: move.move_type != "entry" and move.packaging_material_auto)
        auto.refresh_packaging_material()
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

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._packaging_material_mark_manual()
        return lines

    def write(self, vals):
        res = super().write(vals)
        self._packaging_material_mark_manual()
        return res

    def unlink(self):
        # the invoices have to be read before the lines are gone
        invoices = self.invoice_id
        res = super().unlink()
        invoices._packaging_material_mark_manual_on_invoice()
        return res

    def _packaging_material_mark_manual(self):
        """Take the invoice out of automatic update, the quantities being set by hand."""
        self.invoice_id._packaging_material_mark_manual_on_invoice()
