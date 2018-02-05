# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp


class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    
    date = fields.Datetime(string="Date", related='pick_ids.date',  store=False)
    


