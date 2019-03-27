# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details



from odoo.exceptions import UserError, RedirectWarning
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp

class product_template(models.Model):
    _inherit = 'product.template'

    qty_multiple = fields.Float(
        'Qty Multiple', digits=dp.get_precision('Product Unit of Measure'),
        default=1, required=True,
        help="The sale quantity will be rounded up to this multiple.  If it is 0, the exact quantity will be used.")






