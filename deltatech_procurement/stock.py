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



from openerp.exceptions import except_orm, Warning, RedirectWarning, ValidationError
from openerp import models, fields, api, _
from openerp.tools.translate import _
from openerp import SUPERUSER_ID, api
import openerp.addons.decimal_precision as dp


class stock_picking(models.Model):
    _inherit = "stock.picking"

    physical_transfer = fields.Selection([('none', 'Not required'), ('req', 'Required'), ('done', 'Done')],
                                         string="Status Physical Transfer", default='none', copy=False)

    """
    @api.model
    def default_get(self, fields ):

        res = super(stock_picking, self).default_get(  fields )
        if not res.get('picking_type_id', False):
            context = self.env.context
            if context is None: context = {}
            default_picking_type_code = context.get('default_picking_type_code', [])
            
            try:            
                if default_picking_type_code == 'incoming':
                    picking_type = self.env.ref('stock.picking_type_in')
               
                elif default_picking_type_code == 'outgoing':
                    picking_type = self.env.ref('stock.picking_type_out')
    
                elif default_picking_type_code == 'internal':
                    picking_type = self.env.ref('stock.picking_type_internal')

                elif default_picking_type_code == 'consume':
                    picking_type = self.env.ref('stock.picking_type_consume')    
                                
                if picking_type: 
                    res['picking_type_id'] = picking_type.id
            except:
                pass
        return res
    """

    @api.multi
    def action_confirm(self):
        for picking in self:
            new_follower_ids = []
            msg = ''
            if picking.location_id.user_id:
                new_follower_ids += [picking.location_id.user_id.partner_id.id]
                if picking.location_id.user_id.id <> self.env.user.id:
                    msg = _('Please confirm transfer from %s to %s') % (picking.location_id.name, picking.location_dest_id.name)
            if picking.location_dest_id.user_id:
                new_follower_ids += [picking.location_dest_id.user_id.partner_id.id]                
            if new_follower_ids:
                picking.message_subscribe(new_follower_ids)
            
            if msg and not self.env.context.get('no_message',False):
                #picking.message_post(body=msg,type='comment',subtype='mt_comment')
                document = picking
                message = self.env['mail.message'].with_context({'default_starred':True}).create({
                    'model': 'stock.picking',
                    'res_id': document.id,
                    'record_name': document.name_get()[0][1],
                    'email_from': self.env['mail.message']._get_default_from( ),
                    'reply_to': self.env['mail.message']._get_default_from( ),
                    #'subject': _('Invoice %s') % ( document.name_get()[0][1]),
                    #'body': '%s' % wizard.message,
                    'subject': _('Transfer'),
                    'body': msg,
                     
                    'message_id': self.env['mail.message']._get_message_id(  {'no_auto_thread': True} ),
                    'partner_ids': [(4, id) for id in new_follower_ids],
                    #'notified_partner_ids': [(4, id) for id in new_follower_ids]
                })
                
                
        super(stock_picking, self).action_confirm()
        


    @api.multi
    def action_direct_transfer(self):
        for picking in self:
            picking.with_context({'no_message':True}).action_confirm()
            picking.action_assign()   # verifica disponibilitate
            if not all(move.state == 'assigned' for move in picking.move_lines):
                raise Warning(_('Not all products are available. ')   )
            picking.do_transfer()

    @api.multi
    def confirm_physical_transfer(self):
        msg = _("Physical transfer was made")   
        self.message_post( body= msg)
        self.write({'physical_transfer':'done'})

    @api.multi
    def todo_physical_transfer(self):
        msg = _("It is required Physical Transfer")   
        self.message_post( body= msg)
        self.write({'physical_transfer':'req'})
        
           
    @api.multi
    def rereserve_pick(self):
        res = super(stock_picking, self).rereserve_pick()
        for picking in self:
            msg = ''
            for move in picking.move_lines:
                if move.procure_method=='make_to_order' and move.availability >= 0:  #move.state == 'waiting' 
                    """
                    if round(move.availability, 2) < round(move.product_qty, 2):
                        move_new_id = self.env['stock.move'].split( move=move, qty=move.availability)  
                        move_new = self.browse([move_new_id])
                        move.write({'availability':  0})
                    else:
                    """
                   
                    msg = msg + _('Quantity %s of product %s has bring to order.\n') % ( move.product_qty, move.product_id.name)
                                        
                    move.write({'procure_method':  'make_to_stock',
                                'state':'confirmed',
                                'move_orig_ids':[(6,0,[])]})
                    #move.do_unreserve()
                    move.action_assign()
            self.message_post( subject=_("Rereserve stock"), body= msg)                                                
        return res

    """
    @api.multi
    def rereserve_pick(self):
        msg = _("Rereserve stock")
        self.message_post( body= msg)
        super(stock_picking,self).rereserve_pick()
    """
    
    
    @api.cr_uid_ids_context
    def do_enter_receipt_details(self, cr, uid, picking, context=None):
        return self.do_enter_transfer_details(cr,uid,picking, context )
        
    @api.cr_uid_ids_context
    def do_enter_delivery_details(self, cr, uid, picking, context=None):
        return self.do_enter_transfer_details(cr,uid,picking, context )


    def do_print_picking(self, cr, uid, ids, context=None):
        '''
            This function prints the picking list
            Trebuie tiparit  fiecare document pe formularul lui!
            - Bon de consum -
            - Aviz de expeditie - cu/fara pret
            - Transter intre gestiuni
            - Intrare marfa in stoc ???
        
        '''
        
        context = dict(context or {}, active_ids=ids)       
        return self.pool.get("report").get_action(cr, uid, ids, 'stock.report_picking', context=context)



    def view_current_stock(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display existing stock  .
        '''
        if context is None:
            context = {}
        mod_obj = self.pool.get('ir.model.data')
        dummy, action_id = tuple(mod_obj.get_object_reference(cr, uid, 'stock', 'product_open_quants'))
        action = self.pool.get('ir.actions.act_window').read(cr, uid, action_id, context=context)

        product_ids = []
        for picking in self.browse(cr, uid, ids, context=context):
            product_ids += [move.product_id.id for move in picking.move_lines]
        
        action['context'] = {'search_default_internal_loc': 1, 
                        #     'search_default_product_id': product_ids and product_ids[0] or Falses, 
                             'search_default_locationgroup':1}
        
        action['domain'] = "[('product_id','in',[" + ','.join(map(str, product_ids)) + "])]"

        return action

    @api.one
    @api.constrains('location_id', 'location_dest_id')
    def _check_location(self):
        if self.location_id == self.location_dest_id:
            raise ValidationError("Locations must be different")


class stock_move(models.Model):
    _inherit = 'stock.move'
    
    @api.model
    def default_get(self, fields):
        defaults = super(stock_move, self).default_get(fields)  
        picking_type_id = self.env.context.get('default_picking_type_id', False)
        if picking_type_id:
            central_location = self.env.ref('stock.stock_location_stock')
            my_location = self.env['stock.location'].search([('usage','=','internal'),
                                                             ('user_id','=',self.env.user.id),
                                                             ('id','!=',central_location.id)],
                                                            limit=1)
            my_location = my_location and my_location[0] or False

            if my_location:
                picking_type_internal = self.env.ref('stock.picking_type_internal')
                picking_type_consume = self.env.ref('stock.picking_type_consume')
                picking_type_outgoing_not2binvoiced = self.env.ref('stock.picking_type_outgoing_not2binvoiced')
                
                
                if picking_type_internal and picking_type_id == picking_type_internal.id:
                    defaults['location_dest_id'] = my_location.id
                    
                if picking_type_consume and picking_type_id == picking_type_consume.id:
                    defaults['location_id'] = my_location.id       
    
                if picking_type_outgoing_not2binvoiced and picking_type_id == picking_type_outgoing_not2binvoiced.id:
                    defaults['location_id'] = my_location.id       

                     
        return defaults   
    
    @api.multi
    def do_make_to_stock(self):
        for move in self:
            if move.product_qty > 0 and move.procure_method == 'make_to_order' and round(move.availability, 2) >= round(move.product_qty, 2):
                procurement = self.env['procurement.order'].search([('move_dest_id','=',move.id)])
                if procurement:
                    procurement.cancel() 
                move.procure_method = 'make_to_stock'  
                  
    

    def action_assign(self, cr, uid, ids, context=None):
        #self.do_make_to_stock(cr, uid, ids, context)
        return super(stock_move, self).action_assign(cr, uid, ids, context)



    def action_confirm(self, cr, uid, ids, context=None):
        """
        from https://github.com/aliomattux/make_to_order_check_availability/blob/master/models/stock.py
        """
        #self.do_make_to_stock(cr, uid, ids, context)
        return super(stock_move, self).action_confirm(cr, uid, ids, context)

    
    def _prepare_procurement_from_move(self, cr, uid, move, context=None):
        move_obj = self.pool.get('stock.move')
        def get_parent_move(move_id):
            move = move_obj.browse(cr, uid, move_id)
            if move.move_dest_id:
                return get_parent_move(move.move_dest_id.id)
            return move_id
        
        res = super(stock_move,self)._prepare_procurement_from_move(cr, uid, move, context)
        parent_move_line = get_parent_move(move.id)
        if parent_move_line:
            move = move_obj.browse(cr, uid, parent_move_line)
            partner_name = move.procurement_id and move.procurement_id.sale_line_id and move.procurement_id.sale_line_id.order_id.partner_id.name or False
            name = move.procurement_id and move.procurement_id.sale_line_id and move.procurement_id.sale_line_id.order_id.name or False
            if partner_name:
                res['origin'] = name + ':' +partner_name
        return res
    
    """
    def _create_procurement(self, cr, uid, move, context=None):
        procurement_id = super(stock_move,self)._create_procurement(cr, uid, move, context)
        procurement_obj = self.pool.get('procurement.order')
        
        msg = _("Necesarul a fot generat de miscarea %s") % ( move.picking_id.name)
        procurement_obj.message_post(cr, uid, [procurement_id], body = msg, context=context)
       
        return procurement_id
    """
    
class stock_invoice_onshipping(models.TransientModel):
    _inherit = "stock.invoice.onshipping"
    

    @api.model
    def default_get(self, fields):
        res = super(stock_invoice_onshipping,self).default_get(fields)
        journal_type = self._get_journal_type()
        journals = self.env['account.journal'].search( [('type', '=', journal_type)])
        
        for journal in  journals:
            if journal.user_id.id == self.env.user.id:
                res['journal_id'] = journal.id        
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
