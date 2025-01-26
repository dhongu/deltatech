# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


# Valuation Area
class ValuationArea(models.Model):
    _name = "valuation.area"
    _description = "Valuation Area"

    name = fields.Char(string="Name", required=True, index=True)
    company_id = fields.Many2one(
        "res.company", string="Company", required=True, index=True, default=lambda self: self.env.user.company_id
    )
