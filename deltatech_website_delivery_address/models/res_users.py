# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    delivery_address_id = fields.Many2one("res.partner", string="Delivery Address")
