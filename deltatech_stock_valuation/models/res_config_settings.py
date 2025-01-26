# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, fields, models
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_deltatech_stock_valuation = fields.Boolean("Stock Valuation", readonly=True)
    valuation_area_level = fields.Selection(related="company_id.valuation_area_level", readonly=False)
    valuation_area_id = fields.Many2one(
        "valuation.area", related="company_id.valuation_area_id", string="Valuation Area", readonly=False
    )

    def set_values(self):
        res = super().set_values()
        self.company_id.set_stock_valuation_at_company_level()
        return res

    def refresh_stock_valuation(self):
        if self.valuation_area_level != "company":
            return
        # has group system user
        if not self.env.user.has_group("base.group_system"):
            raise UserError(_("Only System Administrator can do this action!"))
        self.env["product.valuation.history"].recompute_all_amount()
        self.env["product.valuation"].recompute_all_amount()
