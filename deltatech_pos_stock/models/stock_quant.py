from odoo import api, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def write(self, vals):
        # `quantity` (stocul fizic) afectează `qty_available`, deci interesează orice casă.
        # `reserved_quantity` afectează doar `free_qty`, deci notificăm doar casele al căror
        # badge arată disponibilul — rezervările se schimbă la fiecare vânzare și nu merită
        # trimise către casele lăsate pe stoc fizic.
        templates = self.env["product.template"]
        only_available = False
        if "quantity" in vals:
            templates = self._get_pos_templates_to_notify()
        elif "reserved_quantity" in vals and self._pos_available_badge_in_use():
            templates = self._get_pos_templates_to_notify()
            only_available = True
        res = super().write(vals)
        templates._notify_pos_stock_change(only_available_badges=only_available)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        quants = super().create(vals_list)
        quants.filtered("quantity")._get_pos_templates_to_notify()._notify_pos_stock_change()
        return quants

    def _get_pos_templates_to_notify(self):
        return self.product_id.product_tmpl_id.filtered("available_in_pos")

    @api.model
    def _pos_available_badge_in_use(self):
        """Is any register actually showing the available quantity?

        Checked before anything else on the reservation path: `reserved_quantity` is written on
        every reservation, and gathering the products and their templates there would cost every
        installation — including the ones where no register asks for the available quantity,
        which is all of them until someone changes the setting. `pos.config` holds a handful of
        rows, so this is far cheaper than the work it avoids.
        """
        return bool(
            self.env["pos.config"]
            .sudo()
            .search_count(
                [("display_stock", "=", True), ("stock_badge_quantity", "=", "available")],
                limit=1,
            )
        )
