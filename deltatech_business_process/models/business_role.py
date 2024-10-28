# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class BusinessRole(models.Model):
    _name = "business.role"
    _description = "Business Role"

    name = fields.Char(string="Name", required=True)
