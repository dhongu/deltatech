# © 2026 Deltatech
# See README.rst file on the addons root folder for license details


from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _compute_purchase_price(self):
        res = super()._compute_purchase_price()
        for line in self:
            if line.product_id.type == "consu" and line.product_id.bom_ids:
                bom_id = line.get_available_phantom_bom_id()
                if bom_id:
                    purchase_price = line.product_id._compute_bom_price(bom_id, boms_to_recompute=False)

                    # Convert the cost to the line UoM
                    product_cost = line.product_id.uom_id._compute_price(
                        purchase_price,
                        line.product_uom,
                    )

                    line.purchase_price = line._convert_to_sol_currency(product_cost, line.product_id.cost_currency_id)
        return res

    def get_available_phantom_bom_id(self):
        """
        Can be inherited by other modules to provide custom logic for finding phantom BOMs.
        :return: The first "phantom" type Bill of Materials (BOM) associated with the product if available,
                 otherwise False.
        :rtype: Union[object, bool]
        """
        self.ensure_one()
        bom_ids = self.product_id.bom_ids.filtered(
            lambda bom: bom.type == "phantom" and bom.product_id == self.product_id
        )
        if not bom_ids:
            bom_ids = self.product_id.bom_ids.filtered(
                lambda bom: bom.type == "phantom" and bom.product_tmpl_id == self.product_id.product_tmpl_id
            )
        if bom_ids:
            return bom_ids[0]
        return False
