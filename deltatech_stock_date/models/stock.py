# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from datetime import date, datetime
from dateutil import relativedelta

import time
from odoo.exceptions import UserError, RedirectWarning

from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo import SUPERUSER_ID, api

import odoo.addons.decimal_precision as dp

"""
class stock_pack_operation(models.Model):
    _inherit = "stock.pack.operation"

    @api.model
    def create(self,   vals ):

        if vals.get("picking_id"):
            picking = self.env["stock.picking"].browse( vals['picking_id'])
            vals['date'] = picking.min_date  # trebuie sa fie minimul dintre data curenta si data din picking
        res_id = super(stock_pack_operation, self).create( vals)
        return res_id
"""


class stock_quant(models.Model):
    _inherit = "stock.quant"

    """
    @api.model
    def _quant_create_from_move(self, qty, move, lot_id=False, owner_id=False,
                                src_package_id=False, dest_package_id=False,
                                force_location_from=False, force_location_to=False):
        quant = super(stock_quant, self)._quant_create_from_move( qty, move, lot_id=lot_id, owner_id=owner_id,
                                 src_package_id=src_package_id, dest_package_id=dest_package_id,
                                 force_location_from=force_location_from, force_location_to=force_location_to)
        quant.write({'in_date': move.date})
        return quant    
    """

    @api.model
    def _update_available_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None,
                                   in_date=None):
        res = super(stock_quant, self)._update_available_quantity(product_id, location_id, quantity, lot_id, package_id,
                                                                  owner_id, in_date)

        return res


class stock_move(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def write(self, vals):
        date_fields = {'date', 'date_expected'}
        use_date = self.env.context.get('use_date', False)
        if date_fields.intersection(vals):
            if not use_date:
                for move in self:
                    today = fields.Date.today()
                    if 'date' in vals:
                        if move.date_expected.date() < today and move.date_expected < vals['date']:
                            vals['date'] = move.date_expected
                        if move.date.date() < today and move.date < vals['date']:
                            vals['date'] = move.date
                        move.move_line_ids.write({'date': vals['date']})
                        # move.quant_ids.write({'in_date': vals['date']})

                    if 'date_expected' in vals:
                        move_date = vals.get('date', move.date)
                        if move_date.date() < today and move_date < vals['date_expected']:
                            vals['date_expected'] = move_date
            else:

                if 'date' in vals:
                    vals['date'] = use_date
                if 'date_expected' in vals:
                    vals['date_expected'] = use_date

        return super(stock_move, self).write(vals)


class Picking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def action_done(self):
        super(Picking, self).action_done()
        use_date = self.env.context.get('use_date', False)
        if use_date:
            self.write({'date': self.date})
            self.move_lines.write({'date_expected': use_date, 'date': use_date})
            self.move_line_ids.write({'date': use_date})
