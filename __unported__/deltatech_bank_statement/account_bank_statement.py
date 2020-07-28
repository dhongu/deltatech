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
##############################################################################



from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo import SUPERUSER_ID, api



class account_bank_statement_line(models.Model):
    _inherit = "account.bank.statement.line"  
     

    def process_reconciliation(self, cr, uid, id, mv_line_dicts, context=None):
        st_line = self.browse(cr, uid, id, context=context)
        if not st_line.ref:
            name = []
            for line in mv_line_dicts:
                if 'counterpart_move_line_id' in line:
                    name += [line['name']]
            ref = ','.join(name)
            self.write(cr, uid, id, {'ref':ref}, context)
        res = super(account_bank_statement_line, self).process_reconciliation( cr, uid, id, mv_line_dicts, context)
        return res

    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
