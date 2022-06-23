# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.model
    def _update_available_quantity(
        self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, in_date=None
    ):
        if not location_id.allow_negative_stock and location_id.usage == "internal":
            quants = self._gather(
                product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True
            )
            if lot_id and quantity < 0:
                quants = quants.filtered(lambda q: q.lot_id)
                lot_qty = 0.0
                for quant in quants:
                    lot_qty += quant.quantity
            else:
                lot_qty = product_id.with_context(location=location_id.id, compute_child=False).qty_available
            uom_precision_digits = self.env["decimal.precision"].precision_get("Product Unit of Measure")
            result_qty = float_compare(lot_qty + quantity, 0.0, uom_precision_digits)
            if result_qty < 0:
                if location_id.company_id.no_negative_stock:
                    if not lot_id:
                        err = _(
                            "You have chosen to avoid negative stock. %s pieces of %s are remaining in location %s"
                            "but you want to transfer %s pieces. "
                            "Please adjust your quantities or correct your stock with an inventory adjustment."
                        ) % (product_id.qty_available, product_id.name, location_id.name, quantity)
                    else:
                        err = _(
                            "You have chosen to avoid negative stock. %s pieces of %s are remaining in location %s, "
                            "lot %s, but you want to transfer %s pieces. "
                            "Please adjust your quantities or correct your stock with an inventory adjustment."
                        ) % (lot_qty, product_id.name, location_id.name, lot_id.name, quantity)
                    raise UserError(err)

        return super(StockQuant, self)._update_available_quantity(
            product_id, location_id, quantity, lot_id, package_id, owner_id, in_date
        )
