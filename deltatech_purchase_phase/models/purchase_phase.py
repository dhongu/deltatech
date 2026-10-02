# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class PurchaseOrderPhase(models.Model):
    _name = "purchase.order.phase"
    _description = "PurchaseOrderPhase"
    _order = "sequence, name"

    name = fields.Char(translate=True, required=True)
    color = fields.Integer()
    code = fields.Char()

    sequence = fields.Integer()

    action_id = fields.Many2one("ir.actions.server", string="Action")
