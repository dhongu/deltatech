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
                "value": -1 * quantity * self.standard_price,
                "unit_cost": self.standard_price,
                "quantity": -1 * quantity,
            }
            lots = self.env.context["lot_ids"].filtered(lambda l: l.product_id.id == self.id)
            move_lines = self.env.context["move_lines"].filtered(lambda l: l.product_id.id == self.id)
            if lots:
                qty = 0
                amount = 0

                for line in move_lines:
                    amount += line.lot_id.unit_price * line.qty_done
                    qty += line.qty_done

                unit_cost = amount / (qty or 1)
                try:
                    self.with_context(lot_ids=lots)._run_fifo(abs(quantity), company)
                except ZeroDivisionError:
                    pass
                vals["unit_cost"] = round(unit_cost, 2)
                vals["value"] = round(-1 * unit_cost * quantity, 2)
                return vals

        vals = super(ProductProduct, self)._prepare_out_svl_vals(quantity, company)
        return vals

    def _run_fifo(self, quantity, company):
        return super(ProductProduct, self)._run_fifo(quantity, company)

    def _run_fifo_vacuum(self, company=None):
        return super(ProductProduct, self)._run_fifo_vacuum(company)
