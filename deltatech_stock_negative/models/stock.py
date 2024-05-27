# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.model
    def _update_available_quantity(
        self,
        product_id,
        location_id,
        quantity=False,
        reserved_quantity=False,
        lot_id=None,
        package_id=None,
        owner_id=None,
        in_date=None,
    ):
        if not location_id.allow_negative_stock and location_id.usage == "internal":
            quants = self._gather(
                product_id,
                location_id,
                lot_id=lot_id,
                package_id=package_id,
                owner_id=owner_id,
                strict=True,
            )
            if lot_id and quantity - reserved_quantity < 0:
                quants = quants.filtered(lambda q: q.lot_id)
            lot_qty = sum(quants.mapped("quantity"))
            uom_precision_digits = self.env["decimal.precision"].precision_get("Product Unit of Measure")
            result_qty = float_compare(lot_qty + quantity - reserved_quantity, 0.0, uom_precision_digits)
            if result_qty < 0:
                if location_id.company_id.no_negative_stock:
                    if not lot_id:
                        err = _(
                            "You have chosen to avoid negative stock. %(lot_qty)s pieces of %(product_name)s are remaining in location %(location_name)s, "
                            "but you want to transfer %(transfer_qty)s pieces. "
                            "Please adjust your quantities or correct your stock with an inventory adjustment."
                        ) % {
                            "lot_qty": lot_qty,
                            "product_name": product_id.name,
                            "location_name": location_id.name,
                            "transfer_qty": quantity - reserved_quantity,
                        }
                    else:
                        err = _(
                            "You have chosen to avoid negative stock. %(lot_qty)s pieces of %(product_name)s are remaining in location %(location_name)s, "
                            "lot %(lot_name)s, but you want to transfer %(transfer_qty)s pieces. "
                            "Please adjust your quantities or correct your stock with an inventory adjustment."
                        ) % {
                            "lot_qty": lot_qty,
                            "product_name": product_id.name,
                            "location_name": location_id.name,
                            "lot_name": lot_id.name,
                            "transfer_qty": quantity - reserved_quantity,
                        }
                    raise UserError(err)

        return super()._update_available_quantity(
            product_id=product_id,
            location_id=location_id,
            quantity=quantity,
            reserved_quantity=reserved_quantity,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            in_date=in_date,
        )
