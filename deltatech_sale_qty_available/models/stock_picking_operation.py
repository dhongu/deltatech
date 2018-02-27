# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details

from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo import SUPERUSER_ID, api
import odoo.addons.decimal_precision as dp



class PackOperation(models.Model):
    _inherit = "stock.pack.operation"


    qty_available_text = fields.Char(string="Available", compute='_compute_qty_available_text')

    @api.multi
    @api.depends('product_id', 'location_id')
    def _compute_qty_available_text(self):
        for line in self:

            product = line.product_id.with_context(location=line.location_id.id)
            qty_available_text = 'N/A'

            qty_available, virtual_available = product.qty_available, product.virtual_available
            outgoing_qty, incoming_qty = product.outgoing_qty, product.incoming_qty

            if qty_available or virtual_available or outgoing_qty or incoming_qty:
                qty_available_text = "%s = " % virtual_available
                if qty_available:
                    qty_available_text += ' %s ' % qty_available
                if outgoing_qty:
                    qty_available_text += ' -%s ' % outgoing_qty
                if incoming_qty:
                    qty_available_text += ' +%s ' % incoming_qty

            line.qty_available_text = qty_available_text