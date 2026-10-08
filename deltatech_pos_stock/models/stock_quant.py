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
        elif "reserved_quantity" in vals:
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
