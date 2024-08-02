# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    weight_gross = fields.Float("Gross Weight", digits="Stock Weight", help="The gross weight in Kg.")
    weight_net = fields.Float("Net Weight", digits="Stock Weight", help="The net weight in Kg.")

    @api.model
    def create(self, vals_list):
        # Create the sale orders using the default implementation
        sale_orders = super().create(vals_list)

        for sale_order in sale_orders:
            gross_weight = 0.0
            net_weight = 0.0
            # Extract the products from the order lines
            for line in sale_order.order_line:
                # Calculate the new weight
                gross_weight += line.product_id.weight * line.product_uom_qty
                net_weight += line.product_id.l10n_ro_net_weight * line.product_uom_qty
            # Update the weight fields
            sale_order.weight_gross = gross_weight
            sale_order.weight_net = net_weight

        return sale_orders
