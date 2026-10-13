# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    invoice_delivery = fields.Boolean(
        string="Delivery from invoice",
        help="When a customer invoice of this journal is posted, the storable products without a sale order "
        "are added to a new confirmed sale order and delivered from stock, at the invoice date.",
    )
