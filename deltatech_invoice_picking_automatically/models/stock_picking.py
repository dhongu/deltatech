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

    def button_validate(self):
        res = super().button_validate()

        sale_orders = self.env["sale.order"]
        for picking in self:
            if picking.picking_type_id.create_invoice_automatically:
                sale_orders |= picking.sale_id
        if sale_orders:
            invoices = sale_orders._create_invoices(final=True)
            if picking.picking_type_id.post_invoice_automatically:
                invoices.action_post()

        return res
