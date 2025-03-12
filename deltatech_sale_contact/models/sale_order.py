# ©  2008-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_id = fields.Many2one("res.partner", domain=[("parent_id", "=", False)])
    partner_invoice_id = fields.Many2one(
        "res.partner", domain='[ ("parent_id", "=", partner_id), ("type", "=", "invoice")]'
    )
    partner_shipping_id = fields.Many2one(
        "res.partner", domain='[ ("parent_id", "=", partner_id), ("type", "=", "delivery")]'
    )
