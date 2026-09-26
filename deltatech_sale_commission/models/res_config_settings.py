from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sale_user_detail = fields.Selection(
        [("invoice", "Invoice"), ("sale", "Sale order")],
        config_parameter="sale_commission.sale_user_detail",
        default="invoice",
        readonly=False,
    )

    def set_values(self):
        # The margin report view reads the parameter when it is (re)built, so it must be rebuilt
        # after the new value is saved, not on the onchange, which still sees the old value.
        get_param = self.env["ir.config_parameter"].sudo().get_param
        old_value = get_param("sale_commission.sale_user_detail", "invoice")
        res = super().set_values()
        if get_param("sale_commission.sale_user_detail", "invoice") != old_value:
            self.env["sale.margin.report"].init()
        return res
