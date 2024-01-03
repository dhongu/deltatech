# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    valuation_area_id = fields.Many2one("valuation.area", string="Valuation Area")

    def set_valuation_area_id(self):
        for line in self:
            stock_move = line.move_id.stock_move_id
            if line.product_id and line.account_id.stock_valuation:
                valuation_area_level = line.company_id.valuation_area_level
                if valuation_area_level == "company":
                    valuation_area = line.company_id.valuation_area_id
                elif valuation_area_level == "warehouse":
                    valuation_area = stock_move.warehouse_id.valuation_area_id
                elif valuation_area_level == "location":
                    if line.credit:
                        valuation_area = (
                            stock_move.location_id.valuation_area_id or stock_move.location_dest_id.valuation_area_id
                        )
                    else:
                        valuation_area = (
                            stock_move.location_dest_id.valuation_area_id or stock_move.location_id.valuation_area_id
                        )
                else:
                    valuation_area = False

                line.write({"valuation_area_id": valuation_area.id})
