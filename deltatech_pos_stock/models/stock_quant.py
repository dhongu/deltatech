from odoo import api, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def write(self, vals):
        # Doar `quantity` (stocul fizic) afectează `qty_available`; `reserved_quantity`
        # nu schimbă valoarea afișată în badge-ul POS, deci nu merită să declanșeze
        # o notificare (rezervările se schimbă mult mai des decât stocul fizic).
        templates = self._get_pos_templates_to_notify() if "quantity" in vals else self.env["product.template"]
        res = super().write(vals)
        templates._notify_pos_stock_change()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        quants = super().create(vals_list)
        quants.filtered("quantity")._get_pos_templates_to_notify()._notify_pos_stock_change()
        return quants

    def _get_pos_templates_to_notify(self):
        return self.product_id.product_tmpl_id.filtered("available_in_pos")
