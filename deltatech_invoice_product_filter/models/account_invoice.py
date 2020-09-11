# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    # nu mai este necesar acest camp
    # product_id = fields.Many2one('product.product', string='Product', related='invoice_line_ids.product_id')
