# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _

import odoo.addons.base as base
 

GEO_VIEW = ('gmaps', 'GMaps')

if 'gmaps' not in base.ir.ir_actions.VIEW_TYPES:
    base.ir.ir_actions.VIEW_TYPES.append(GEO_VIEW )


class IrUIView(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(selection_add=[GEO_VIEW])
    
    """
    def __init__(self, pool, cursor):
        #Hack due to the lack of selection fields inheritance mechanism.
        super(IrUIView, self).__init__(pool, cursor)
        #type_selection = self._columns['type'].selection
        if self._columns:
            type_selection = self._columns['type'].selection  
            if GEO_VIEW not in type_selection:
                tmp = list(type_selection)
                tmp.append(GEO_VIEW)
                tmp.sort()
                self._columns['type'].selection = tuple(set(tmp))

    
    _columns = {
        'type': fields.selection([
            ('tree','Tree'),
            ('form','Form'),
            ('graph', 'Graph'),
            ('calendar', 'Calendar'),
            ('diagram','Diagram'),
            ('gantt', 'Gantt'),
            ('kanban', 'Kanban'),
            ('search','Search'),
            ('gmaps', 'GMaps'),
            ('qweb', 'QWeb')], string='View Type'),
    }
    """
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: