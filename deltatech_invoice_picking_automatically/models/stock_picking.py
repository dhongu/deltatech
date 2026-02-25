# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    create_invoice_automatically = fields.Boolean(string="Create Invoice Automatically")
    post_invoice_automatically = fields.Boolean(string="Post Invoice Automatically", default=True)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        res = super()._action_done()

        sale_orders = self.env["sale.order"]
        for picking in self:
            if picking.picking_type_id.create_invoice_automatically:
                sale_orders |= picking.sale_id
        if sale_orders:
            sale_orders.order_line._compute_qty_delivered()
            invoices = sale_orders._create_invoices(final=True)
            for picking in self:
                if picking.picking_type_id.post_invoice_automatically:
                    # we should filter invoices to post only those related to this picking's sale order
                    # but _create_invoices might group them.
                    # for simplicity and following previous logic, we post all created invoices
                    # if at least one picking that triggered invoicing has post_invoice_automatically
                    invoices.filtered(lambda i: i.state == "draft").action_post()
                    break

        return res
