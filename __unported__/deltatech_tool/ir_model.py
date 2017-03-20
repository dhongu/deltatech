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

from odoo.osv import fields,osv
from odoo import tools
from odoo import models
 

class ir_model_fields(osv.osv):
    _inherit = 'ir.model.fields'

    def _drop_column(self, cr, uid, ids, context=None):
        
        for field in self.browse(cr, uid, ids, context):
            if field.name in MAGIC_COLUMNS:
                continue
            model = self.pool[field.model]
            cr.execute('select relkind from pg_class where relname=%s', (model._table,))
            result = cr.fetchone()
            cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name ='%s' and column_name='%s'" %(model._table, field.name))
            column_name = cr.fetchone()
            if column_name and (result and result[0] == 'r') and 1==2:
                cr.execute('ALTER table "%s" DROP column "%s" cascade' % (model._table, field.name))
            # remove m2m relation table for custom fields
            # we consider the m2m relation is only one way as it's not possible
            # to specify the relation table in the interface for custom fields
            # TODO master: maybe use ir.model.relations for custom fields
            if field.state == 'manual' and field.ttype == 'many2many' and 1==2:
                rel_name = model._fields[field.name].relation
                cr.execute('DROP table "%s"' % (rel_name))
            model._pop_field(field.name)

        return True   
    
        """ Original
        for field in self.browse(cr, uid, ids, context):
            if field.name in MAGIC_COLUMNS:
                continue
            model = self.pool[field.model]
            cr.execute('select relkind from pg_class where relname=%s', (model._table,))
            result = cr.fetchone()
            cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name ='%s' and column_name='%s'" %(model._table, field.name))
            column_name = cr.fetchone()
            if column_name and (result and result[0] == 'r'):
                cr.execute('ALTER table "%s" DROP column "%s" cascade' % (model._table, field.name))
            # remove m2m relation table for custom fields
            # we consider the m2m relation is only one way as it's not possible
            # to specify the relation table in the interface for custom fields
            # TODO master: maybe use ir.model.relations for custom fields
            if field.state == 'manual' and field.ttype == 'many2many':
                rel_name = model._fields[field.name].relation
                cr.execute('DROP table "%s"' % (rel_name))
            model._pop_field(field.name)

        return True        
        """
        """ V7
        for field in self.browse(cr, uid, ids, context):
            model = self.pool.get(field.model)
            cr.execute('select relkind from pg_class where relname=%s', (model._table,))
            result = cr.fetchone()
            cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name ='%s' and column_name='%s'" %(model._table, field.name))
            column_name = cr.fetchone()
            if column_name and (result and result[0] == 'r') and 1==2:
                cr.execute('ALTER table "%s" DROP column "%s" cascade' % (model._table, field.name))
            model._columns.pop(field.name, None)\
        return True
        """


ir_model_fields()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

