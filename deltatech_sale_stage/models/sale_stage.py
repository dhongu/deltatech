# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class SaleOrderStage(models.Model):
    _name = "sale.order.stage"
    _description = "SaleOrderStage"
    _order = "sequence, name"

    name = fields.Char()
    color = fields.Integer()

    sequence = fields.Integer()
    send_email = fields.Boolean()  # comanda a fost transmisa catre client
    confirmed = fields.Boolean()  # comanda a fost confirmata
    delivered = fields.Boolean()  # comanda a fost livrata
    invoiced = fields.Boolean()  # comanda a fost facturata
    paid = fields.Boolean()  # comanda a fost platita

    action_id = fields.Many2one("ir.server.action", string="Action")
