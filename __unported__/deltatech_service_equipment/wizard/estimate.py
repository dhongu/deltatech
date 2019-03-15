# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
import odoo.addons.decimal_precision as dp
from odoo.api import Environment
import threading


class service_meter_reading_estimate(models.TransientModel):
    _name = 'service.meter.reading.estimate'
    _description = "Meter Reading Estimate"

    period_id = fields.Many2one('account.period', string='Period', domain=[('state', '!=', 'done')],required=True,) 

    meter_ids = fields.Many2many('service.meter', 'service_meter_estimate', 'estimate_id', 'meter_id', string='Meters')


    @api.model
    def default_get(self, fields):      
        defaults = super(service_meter_reading_estimate, self).default_get(fields)
          
        active_ids = self.env.context.get('active_ids', False)
         
        if active_ids:
            domain=[('id','in', active_ids )]   
        else:
            domain=[]
        res = self.env['service.meter'].search(domain)
        defaults['meter_ids'] = [ (6,0,[rec.id for rec in res]) ]
        return defaults    
    
    
 
    def do_estimation(self, cr, uid, ids, context=None):
        threaded_estimation = threading.Thread(target=self._background_estimation, args=(cr, uid, ids, context))
        threaded_estimation.start()        
        return {'type': 'ir.actions.act_window_close'}





    def _background_estimation(self, cr, uid, ids, context=None):
        """
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: List of IDs selected
        @param context: A standard dictionary
        """
        with Environment.manage():
            new_cr = self.pool.cursor()
            self._calc_estimation(new_cr, uid, ids, context)
            new_cr.commit()
            new_cr.close()
            
        return {}        
           
    @api.multi
    def _calc_estimation(self):
         
        domain_date = [('date','>=',self.period_id.date_start),('date','<=',self.period_id.date_end)]
        for meter in self.meter_ids:
            domain = domain_date + [('meter_id','=',meter.id)]
            reading = self.env['service.meter.reading'].search(domain, limit=1)
            if not reading:
                reading = self.env['service.meter.reading'].create({'meter_id':meter.id,
                                                            'equipment_id':meter.equipment_id.id,
                                                            'date':self.period_id.date_end,
                                                            'counter_value':meter.get_forcast(self.period_id.date_end),
                                                            'estimated':True})
             
         
        message = _('Estimation executed in background was terminated')
        self.env.user.post_notification(title=_('Estimation'),message=message)   

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
