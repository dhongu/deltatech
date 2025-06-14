# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models, fields


TRANSACTION_KEYS = [
    ('WRX', 'Goods Receipt from Supplier'),
    ('VAX', 'Goods Issue to Customer'),
    ('ZTR', 'Internal Transfer'),
    ('GBB', 'Consumption'),
]

class ProductAccountDetermination(models.Model):
    _name = "product.account.determination"
    _description = "Product Account Determination"

    transaction_key = fields.Selection(
        selection=TRANSACTION_KEYS,
        string="Transaction Key",
        required=True,
        default='GBB'
    )
    account_modifier_id = fields.Many2one("account.modifier", string="Account Modifier")
    valuation_class_id = fields.Many2one("product.valuation.class", string="Valuation Class")
    valuation_area_id = fields.Many2one("product.valuation.area", string="Valuation Area")
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)

    debit_account_id = fields.Many2one("account.account", string="Debit Account", required=True)
    credit_account_id = fields.Many2one("account.account", string="Credit Account", required=True)
