# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    gln = fields.Char(string="GLN", help="Global Location Number")
