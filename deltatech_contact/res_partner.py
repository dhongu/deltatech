# -*- coding: utf-8 -*-
##############################################################################
#
#     Romanian accounting localization for OpenERP V7
#        @author -  Fekete Mihai, Tatár Attila <atta@nvm.ro>
#     Copyright (C) 2011-2013 TOTAL PC SYSTEMS (http://www.www.erpsystems.ro). 
#     Copyright (C) 2013 Tatár Attila
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

from openerp import models, fields, api, tools, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp
from openerp.api import Environment


class res_partner(models.Model):
    _inherit = 'res.partner'


    def check_cnp(self, cr, uid, ids, context=None):
        
        for contact in self.browse(cr, uid, ids, context=context):
            if not contact.cnp:
                return True
            cnp = contact.cnp
            if (len(cnp) != 13):
                return False
            key = '279146358279';
            suma = 0
            for i in range(len(key)):
                suma +=  int(cnp[i])*int(key[i])
    
            if (suma % 11 == 10):
                rest = 1
            else:
                rest = suma % 11
                
            if (rest == int(cnp[12])):
                return True
            else:
                return False

    def cnp_change(self, cr, uid, ids, value, context=None):
        v = {}
        try:
            if value:
                v['birthdate'] =time.strftime("%Y-%m-%d", time.strptime(value[1:7],"%y%m%d")) 
        except:   
            v = {}   # de adaugat mesaj de atentionare
        return {'value':v}
  
  
    def birthdate_change(self, cr, uid, ids, value, context=None):
        v = {}
        if value:
            for contact in self.browse(cr, uid, ids, context=context):
                try:
                    if contact.cnp: 
                        cnp = contact.cnp                             
                        cnp = cnp[0] + time.strftime("%y%m%d", time.strptime(value, "%Y-%m-%d")) + cnp[7:12]                       
                        key = '279146358279';
                        suma = 0
                        for i in range(len(key)):
                            suma +=  int(cnp[i])*int(key[i])      
                        if (suma % 11 == 10):
                            rest = 1
                        else:
                            rest = suma % 11                   
                        v['cnp'] = cnp + str(rest)
                except:   
                    v = {}   # de adaugat mesaj de atentionare                
        return {'value':v}



    @api.one
    @api.depends('type', 'is_company')
    def _compute_is_department(self):
        if self.is_company or self.type == 'contact': 
            self.is_department = False
        else:
            self.is_department = True
                

    cnp = fields.Char(string='CNP', size=13)
    id_nr = fields.Char(string='ID Nr', size=12)
    id_issued_by = fields.Char(string='ID Issued by', size=20)
    mean_transp = fields.Char(string='ID Issued by', size=12)
    is_department = fields.Boolean(string='Is department', compute='_compute_is_department')


 
 
    _defaults = {'user_id': lambda self, cr, uid, context: uid} 
    _constraints = [(check_cnp, _("CNP invaid"), ["cnp"]), ]


    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = record.name
            if record.parent_id and not record.is_company and record.type != 'contact': 
                    name = "%s, %s" % (record.parent_name, name)
            if context.get('show_address_only'):
                name = self._display_address(cr, uid, record, without_company=True, context=context)
            if context.get('show_address'):
                name = name + "\n" + self._display_address(cr, uid, record, without_company=True, context=context)
            name = name.replace('\n\n','\n')
            name = name.replace('\n\n','\n')
            if context.get('show_email') and record.email:
                name = "%s <%s>" % (name, record.email)
            res.append((record.id, name))
        return res
 




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
