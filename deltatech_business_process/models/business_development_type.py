# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class BusinessDevelopmentType(models.Model):
    _name = "business.development.type"
    _description = "Business Development Type"

    name = fields.Char(string="Name", required=True)
