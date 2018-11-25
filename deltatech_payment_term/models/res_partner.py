# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details


 
from odoo import models, fields, api, _
from odoo.exceptions import  Warning, RedirectWarning

 
 


class res_partner(models.Model):
    _inherit = "res.partner"
    
 
    @api.multi
    def view_rate(self):
        action = self.env.ref('deltatech_payment_term.action_account_moves_sale').read()[0]         
        action['domain'] = "[('partner_id','=',"+str(self.id)+" )]"        
        return action          
 
            

