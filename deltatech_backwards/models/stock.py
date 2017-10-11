# coding=utf-8



from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang

from odoo.exceptions import UserError, RedirectWarning, ValidationError

import odoo.addons.decimal_precision as dp




class StockPicking(models.Model):
    _inherit = "stock.picking"


    invoice_state = fields.Selection([("invoiced", "Invoiced"),
                                      ("2binvoiced", "To Be Invoiced"),
                                      ("none", "Not Applicable")
                                      ], string="Invoice Control", readonly=True)