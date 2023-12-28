from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sale_user_detail = fields.Selection(
        [("invoice", "Invoice"), ("sale", "Sale order")],
        config_parameter="sale_commission.sale_user_detail",
        default="invoice",
        readonly=False,
    )

    @api.onchange("sale_user_detail")
    def _onchange_sale_user_detail(self):
        self.env["sale.margin.report"].init()
