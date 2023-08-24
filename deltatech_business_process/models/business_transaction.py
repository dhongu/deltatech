# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class BusinessTransaction(models.Model):
    _name = "business.transaction"
    _description = "Business transaction"

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    area_id = fields.Many2one("business.area", string="Business Area")
