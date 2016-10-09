# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Deltatech All Rights Reserved
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
##############################################################################



from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp


class service_change_invoice_date(models.TransientModel):
    _name = 'service.change.invoice.date'
    _description = "Service change invoice date"
 
    date_invoice = fields.Date(string='Invoice Date') 



    @api.model
    def default_get(self, fields):
        defaults = super(service_change_invoice_date, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', False) 
        if active_ids:
            cons = self.env['service.consumption'].browse(active_ids[0])
            defaults['date_invoice'] = cons.date_invoice
        return defaults   



    @api.multi
    def do_change(self):
        active_ids = self.env.context.get('active_ids', False)

        domain=[('invoice_id', '=', False),('id','in', active_ids )]   
            
        consumptions = self.env['service.consumption'].search(domain)
        
        if not consumptions:
            raise except_orm(_('No consumptions!'),
                             _("There were no service consumption !"))
            
        consumptions.write({'date_invoice':self.date_invoice})
        
        
        return {
            'domain': "[('id','in', ["+','.join(map(str,[rec.id for rec in consumptions]))+"])]",
            'name': _('Service Consumption'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'service.consumption',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: 