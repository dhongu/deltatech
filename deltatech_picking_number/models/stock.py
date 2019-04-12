# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo.exceptions import UserError, RedirectWarning
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo import SUPERUSER_ID, api
import odoo.addons.decimal_precision as dp


class stock_picking(models.Model):
    _inherit = "stock.picking"

    request_number = fields.Char(string='Request Number')

    @api.multi
    def action_get_number(self):
        if not self.request_number:
            if self.picking_type_id.request_sequence_id:
                request_number = self.picking_type_id.request_sequence_id.next_by_id()
                if request_number:
                    self.write({'request_number': request_number,
                                'name': request_number})

    @api.multi
    def unlink(self):
        for picking in self:
            if picking.request_number:
                raise UserError(_('The document %s has been numbered') % picking.request_number)
        return super(stock_picking, self).unlink()


class stock_picking_type(models.Model):
    _inherit = "stock.picking.type"

    request_sequence_id = fields.Many2one('ir.sequence', string='Sequence on Request')
