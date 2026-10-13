# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    allow_negative_stock = fields.Boolean(string="Allow Negative Stock")
    check_serial_no = fields.Boolean(
        default=True,
        string="Check Serial No.",
        help="If checked, the no-negative-stock check of serial-tracked products is done per serial number. "
        "If unchecked, it is done on the total of all serial numbers in the location, and reservation ignores the "
        "serial number.",
    )
