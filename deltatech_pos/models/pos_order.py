# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError

import base64

class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.multi
    def create_missing_picking(self):
        orders = self
        if not orders:
            orders = self.search([('picking_id', '=', False)], order="date_order")
        for order in orders:
            if not order.picking_id:
                try:
                    order.create_picking()
                    _logger.info("%s %s" % (order.name, order.picking_id.name or ''))

                    if order.picking_id:
                        order.picking_id.write({'min_date': order.date_order})
                        order.picking_id.move_lines.write({'create_date': order.date_order,
                                                           'date_expected': order.date_order,
                                                           'date': order.date_order})
                    self.env.cr.commit()
                except:
                    pass


