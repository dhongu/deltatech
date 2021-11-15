# ©  2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class SetProductTradeMarkup(models.TransientModel):
    _name = "product.markup.wizard"
    _description = "product.markup.wizard"

    selected_line = fields.Boolean()
    partner_id = fields.Many2one("res.partner")
    trade_markup = fields.Float(string="Trade Markup")

    def do_set_trade_markup(self):
        if self.selected_line:
            active_ids = self.env.context.get("active_ids")
            products = self.env["product.template"].browse(active_ids)
        else:
            domain = [("name", "=", self.partner_id.id)]
            supplierinfo = self.env["product.supplierinfo"].search(domain)
            products = self.env["product.template"]
            for item in supplierinfo:
                products |= item.product_tmpl_id
                products |= item.product_id.product_tmpl_id

        products.write({"trade_markup": self.trade_markup})
        products.onchange_last_purchase_price()
