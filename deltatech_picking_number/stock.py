# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com 
#                    Kyle Waid  <kyle.waid(@)gcotech(.)com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################



from odoo.exceptions import except_orm, Warning, RedirectWarning
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
                    self.write({'request_number':request_number,
                                'name':request_number})

    @api.multi
    def unlink(self):
        for picking in self:
            if picking.request_number:
                raise Warning(_('The document %s has been numbered') % picking.request_number )
        return super(stock_picking,self).unlink()
        

class stock_picking_type(models.Model):
    _inherit = "stock.picking.type"
    request_sequence_id  =  fields.Many2one('ir.sequence', string='Sequence on Request' )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
