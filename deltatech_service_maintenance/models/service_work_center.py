# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ServiceWorkCenter(models.Model):
    _name = "service.work.center"
    _description = "Service Work Center"

    name = fields.Char()
    location_id = fields.Many2one("stock.location")
    sale_route_id = fields.Many2one("stock.route", string="Sale Route")
    color = fields.Integer("Color")
    picking_type_id = fields.Many2one("stock.picking.type")
    transfer_route_id = fields.Many2one("stock.route", string="Transfer Route")
    costs_hour = fields.Float(string="Cost per hour", help="Specify cost of work center per hour.", default=0.0)
