# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _prepare_out_svl_vals(self, quantity, company):

        if "lot_ids" in self.env.context:
            vals = {
                "product_id": self.id,
                "value": quantity * self.standard_price,
                "unit_cost": self.standard_price,
                "quantity": quantity,
            }
            lots = self.env.context["lot_ids"].filtered(lambda l: l.product_id.id == self.id)
            if lots:
                if self.tracking == "serial":
                    qty = 0.0
                    amount = 0.0
                    for lot in lots:
                        amount += lot.inventory_value
                        qty += 1
                    unit_cost = amount / qty
                else:
                    quants = self.env["stock.quant"]
                    for lot in lots:
                        quants |= lot.quant_ids

                    qty = 0
                    amount = 0
                    for quant in quants:
                        if quant.quantity > 0:
                            amount += quant.value
                            qty += quant.quantity
                    unit_cost = amount / (qty or 1)
                vals["unit_cost"] = round(unit_cost, 2)
                vals["value"] = round(unit_cost * quantity, 2)
            return vals

        vals = super(ProductProduct, self)._prepare_out_svl_vals(quantity, company)
        return vals

    def _run_fifo(self, quantity, company):
        return super(ProductProduct, self)._run_fifo(quantity, company)

    def _run_fifo_vacuum(self, company=None):
        return super(ProductProduct, self)._run_fifo_vacuum(company)
