# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models, _




class PackOperation(models.Model):
    _inherit = "stock.pack.operation"

    @api.model
    def create(self, vals):
        vals['qty_done'] = vals.get('product_qty')
        return super(PackOperation, self).create(vals)

