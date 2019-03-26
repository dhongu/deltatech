# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details



from odoo.exceptions import UserError, RedirectWarning
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo import SUPERUSER_ID, api
import odoo.addons.decimal_precision as dp


class sale_order(models.Model):
    _inherit = 'sale.order'

    is_ready = fields.Boolean(string='Is ready', compute="_compute_is_ready")

    @api.multi
    def _compute_is_ready(self):
        for order in self:
            is_ready = order.state in ['sent', 'sale', 'progress']
            if is_ready:
                for line in order.order_line:
                    is_ready = is_ready and (line.qty_available >= line.product_uom_qty)
            order.is_ready = is_ready



class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    qty_available = fields.Float(related='product_id.qty_available', string='Quantity On Hand')
    virtual_available = fields.Float(related='product_id.virtual_available', string='Forecast Quantity')
    qty_available_text = fields.Char(string="Available", compute='_compute_qty_available_text')

    @api.multi
    @api.depends('product_id', 'route_id')
    def _compute_qty_available_text(self):
        for line in self:
            product = line.product_id
            if line.route_id:
                location = False
                for pull in line.route_id.pull_ids:
                    location = pull.location_src_id
                if location:
                    product = line.product_id.with_context(location=location.id)
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