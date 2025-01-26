# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id, description):
        res = super()._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
        for line in res:
            product_id = line[2].get("product_id")
            account_id = line[2].get("account_id")
            stock_valuation = self.env["account.account"].browse(account_id).stock_valuation
            if product_id and stock_valuation:
                valuation_area_level = self.company_id.valuation_area_level
                if valuation_area_level == "company":
                    valuation_area = self.company_id.valuation_area_id
                elif valuation_area_level == "warehouse":
                    valuation_area = self.warehouse_id.valuation_area_id
                elif valuation_area_level == "location":
                    if line[2].get("debit"):
                        valuation_area = self.location_id.valuation_area_id or self.location_dest_id.valuation_area_id
                    else:
                        valuation_area = self.location_dest_id.valuation_area_id or self.location_id.valuation_area_id
                else:
                    valuation_area = False

                if valuation_area:
                    line[2].update({"valuation_area_id": valuation_area.id})
        return res

    # pretul de iesire din stoc se va calula in functie de aria de evaluare
    def _get_price_unit(self):
        return super()._get_price_unit()
