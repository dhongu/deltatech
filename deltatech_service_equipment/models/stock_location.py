# ©  2015-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    rental = fields.Boolean()
