# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    weight_gross = fields.Float("Gross Weight", digits="Stock Weight", help="The gross weight in Kg.")
    weight_net = fields.Float("Net Weight", digits="Stock Weight", help="The net weight in Kg.")

    @api.model_create_multi
    def create(self, vals_list):
        # Create the sale orders using the default implementation
        sale_orders = super().create(vals_list)

        for sale_order in sale_orders:
            gross_weight = 0.0
            net_weight = 0.0
            # Extract the products from the order lines
            for line in sale_order.order_line:
                # Calculate the new weight
                if not line.product_id:
                    continue
                line_gross, line_net = line.product_id._get_line_weights(line.product_uom_qty, line.product_uom_id)
                gross_weight += line_gross
                net_weight += line_net
            # Update the weight fields
            sale_order.weight_gross = gross_weight
            sale_order.weight_net = net_weight

        return sale_orders
