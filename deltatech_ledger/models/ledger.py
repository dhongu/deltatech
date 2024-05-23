from odoo import models, fields


class Ledger(models.Model):
    _name = 'ledger.ledger'

    name = fields.Char('Name')
    description = fields.Text('Description')
