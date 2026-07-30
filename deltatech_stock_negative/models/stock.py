# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, models
from odoo.exceptions import UserError


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def _get_available_quantity(
        self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, strict=False, allow_negative=False
    ):
        # This is a plain read/compute helper called from many places (forecast
        # availability on lists/kanban, reservation math, inventory adjustments...).
        # It must stay side-effect free: the "no negative stock" rule is enforced
        # only at actual move validation time, in StockMoveLine._action_done().
        if (
            location_id
            and not location_id.allow_negative_stock
            and not location_id.check_serial_no
            and product_id.tracking == "serial"
        ):
            lot_id = None
        return super()._get_available_quantity(
            product_id=product_id,
            location_id=location_id,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            strict=strict,
            allow_negative=allow_negative,
        )


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _action_done(self):
        self._check_no_negative_stock()
        return super()._action_done()

    def _check_no_negative_stock(self):
        """Block only the actual validation of a move, not the browsing of
        stock or the correction of an existing deviation via an inventory
        adjustment (that flow does not go through here).

        Checked against the raw physical `quantity` on the quant, not the
        `available_quantity` (quantity minus reserved): this move already
        holds its own reservation on that quant, so netting reservations out
        here would count the move's own reservation as competing demand.
        """
        Quant = self.env["stock.quant"]
        for ml in self:
            location = ml.location_id
            if not location or location.usage != "internal" or location.allow_negative_stock:
                continue
            company = ml.company_id or self.env.company
            if not company.no_negative_stock:
                continue
            quantity = ml.product_uom_id._compute_quantity(ml.quantity, ml.product_id.uom_id, rounding_method="HALF-UP")
            if ml.product_id.uom_id.compare(quantity, 0) <= 0:
                continue
            lot_id = ml.lot_id
            if ml.product_id.tracking == "serial" and not location.check_serial_no:
                lot_id = None
            domain = [
                ("product_id", "=", ml.product_id.id),
                ("location_id", "=", location.id),
                ("lot_id", "=", lot_id.id if lot_id else False),
                ("package_id", "=", ml.package_id.id if ml.package_id else False),
                ("owner_id", "=", ml.owner_id.id if ml.owner_id else False),
            ]
            physical_qty = sum(Quant.sudo().search(domain).mapped("quantity"))
            if ml.product_id.uom_id.compare(physical_qty - quantity, 0) < 0:
                raise UserError(
                    _(
                        "You have chosen to avoid negative stock. %(lot_qty)s pieces of %(product_name)s"
                        " are remaining in location %(location_name)s. "
                        "Please adjust your quantities or correct your stock with an inventory adjustment."
                    )
                    % {
                        "lot_qty": physical_qty - quantity,
                        "product_name": ml.product_id.name,
                        "location_name": location.name,
                    }
                )
