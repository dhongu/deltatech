# -*- coding: utf-8 -*-
# ©  2008-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context


class ProductReplenish(models.TransientModel):
    _inherit = 'product.replenish'

    supplier_id = fields.Many2one('product.supplierinfo' )

    def _prepare_run_values(self):
        values = super(ProductReplenish, self)._prepare_run_values()
        values['supplier_id'] = self.supplier_id
        return values