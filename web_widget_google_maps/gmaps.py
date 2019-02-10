# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _

from odoo.addons import base
 

GEO_VIEW = ('gmaps', 'GMaps')

if 'gmaps' not in base.ir.ir_actions.VIEW_TYPES:
    base.ir.ir_actions.VIEW_TYPES.append(GEO_VIEW )


class IrUIView(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(selection_add=[GEO_VIEW])
    
