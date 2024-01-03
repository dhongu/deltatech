# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # valuation_level se poate modifica daca nu sunt facute miscari de stoc
    valuation_area_level = fields.Selection(
        [("company", "Company"), ("warehouse", "Warehouse"), ("location", "Location")],
        string="Valuation Area Level",
        default="company",
    )
    valuation_lot_level = fields.Boolean(string="Valuation Lot Level", default=False)
    valuation_area_id = fields.Many2one("valuation.area", string="Valuation Area")

    def set_stock_valuation_at_company_level(self):
        self.ensure_one()
        if self.valuation_area_level != "company":
            return

        if not self.valuation_area_id:
            valuation_area = self.env["valuation.area"].create(
                {
                    "name": self.name,
                    "company_id": self.id,
                }
            )
            self.valuation_area_id = valuation_area.id

        domain = [("property_stock_valuation_account_id", "!=", False)]
        categories = self.env["product.category"].search(domain)
        accounts = categories.mapped("property_stock_valuation_account_id")
        accounts.write({"stock_valuation": True})
        accounts = self.env["account.account"].search([("stock_valuation", "=", True)])
        params = {
            "account_ids": tuple(accounts.ids),
            "valuation_area_id": self.valuation_area_id.id,
        }

        self.env.cr.execute(
            """
                UPDATE account_move_line SET valuation_area_id = %(valuation_area_id)s
                where account_id in %(account_ids)s;
            """,
            params,
        )
