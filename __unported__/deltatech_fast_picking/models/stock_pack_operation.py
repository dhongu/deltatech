# coding=utf-8

from odoo import api, fields, models, _

from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round, float_compare


class PackOperation(models.Model):
    _inherit = "stock.pack.operation"

    @api.model
    def create(self, vals):
        vals['qty_done'] = vals.get('product_qty')
        return super(PackOperation, self).create(vals)

