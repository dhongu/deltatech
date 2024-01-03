# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, fields, models
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_deltatech_valuation = fields.Boolean("Stock Valuation", readonly=True)
    valuation_area_level = fields.Selection(related="company_id.valuation_area_level", readonly=False)
    valuation_area_id = fields.Many2one(
        "valuation.area", related="company_id.valuation_area_id", string="Valuation Area", readonly=False
    )

    def set_values(self):
        super().set_values()
        if self.valuation_area_level != "company":
            return

        if not self.valuation_area_id:
            valuation_area = self.env["valuation.area"].create(
                {
                    "name": self.company_id.name,
                    "company_id": self.company_id.id,
                }
            )
            self.company_id.valuation_area_id = valuation_area.id

        domain = [("property_stock_valuation_account_id", "!=", False)]
        categories = self.env["product.category"].search(domain)
        accounts = categories.mapped("property_stock_valuation_account_id")
        accounts.write({"stock_valuation": True})
        accounts = self.env["account.account"].search([("stock_valuation", "=", True)])
        params = {
            "account_ids": tuple(accounts.ids),
            "valuation_area_id": self.company_id.valuation_area_id.id,
        }

        self.env.cr.execute(
            """
                UPDATE account_move_line SET valuation_area_id = %(valuation_area_id)s
                where account_id in %(account_ids)s and valuation_area_id != %(valuation_area_id)s
            """,
            params,
        )

    def refresh_stock_valuation(self):
        if self.valuation_area_level != "company":
            return
        # has group system user
        if not self.env.user.has_group("base.group_system"):
            raise UserError(_("Only System Administrator can do this action!"))
        self.env["product.valuation.history"].recompute_all_amount()
        self.env["product.valuation"].recompute_all_amount()
