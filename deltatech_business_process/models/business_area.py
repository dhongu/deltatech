# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class BusinessArea(models.Model):
    _name = "business.area"
    _description = "Business Area"

    name = fields.Char(string="Name", required=True)
