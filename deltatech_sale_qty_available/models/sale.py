# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_ready = fields.Boolean(string="Is ready", compute="_compute_is_ready")

    # aceasta functie poate sa fie consumatoare de resurse !
    # trebuie sa scaneze stocurile pentru toate produsele din comenzile de vanzare afisate

    def _compute_is_ready(self):
        for order in self:

            is_ready = order.state in ["draft", "sent", "sale", "done"] and order.invoice_status != "invoiced"
            if is_ready:
                for line in order.order_line:
                    is_ready = is_ready and (line.qty_available_today >= line.product_uom_qty)
            order.is_ready = is_ready
