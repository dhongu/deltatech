# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com       
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
#
##############################################################################


from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp


class stock_picking(models.Model):
    _inherit = "stock.picking"

    
    @api.model
    @api.returns('self', lambda value:value.id)
    def create(self, vals):
        picking = super(stock_picking, self).create(vals)
        notification_id = self.env.context.get('notification_id',False)
        if notification_id:
            notification =  self.env['service.notification'].browse(notification_id)
            notification.write({'piking_id': picking.id})
        return picking
        
    



#todo:  raport cu piesele consumate pe fiecare echipament / contract - raportat cu numarul de pagini tiparite 
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: