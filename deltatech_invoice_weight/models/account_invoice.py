# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    weight = fields.Float("Gross Weight", digits="Stock Weight", help="The gross weight in Kg.")
    weight_net = fields.Float("Net Weight", digits="Stock Weight", help="The net weight in Kg.")
    weight_package = fields.Float("Package Weight", digits="Stock Weight")
