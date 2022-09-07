# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    no_negative_stock = fields.Boolean(
        string="No negative stock", default=True, help="Allows you to prohibit negative stock quantities."
    )
    force_effective_qty = fields.Boolean(
        string="Set Effective Qty", default=False, help="Set effective quantity in picking when use negative stock."
    )


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    no_negative_stock = fields.Boolean(
        related="company_id.no_negative_stock",
        string="No negative stock",
        readonly=False,
        help="Allows you to prohibit negative stock quantities.",
    )
    force_effective_qty = fields.Boolean(
        related="company_id.force_effective_qty",
        readonly=False,
        string="Set Effective Qty",
        help="Set effective quantity in picking when use negative stock.",
    )
