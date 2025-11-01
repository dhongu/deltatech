# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    allow_negative_stock = fields.Boolean(string="Allow Negative Stock")
    check_serial_no = fields.Boolean(
        default=True,
        string="Check Serial No.",
        help="If checked, the serial numbers will be checked on the moves and an error will be raised if the serial number is reserved on another move or is unavailable.",
    )
