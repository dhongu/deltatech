# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    stage_id = fields.Many2one("sale.order.stage", string="Stage")


class SaleOrderStage(models.Model):
    _name = "sale.order.stage"
    _description = "SaleOrderStage"

    name = fields.Char()
    color = fields.Integer()

    delivery = fields.Boolean()
    invoice = fields.Boolean()
    paid = fields.Boolean()
    send_email = fields.Boolean()
