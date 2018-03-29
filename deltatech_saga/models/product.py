# -*- coding: utf-8 -*-
# ©  2017 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
import math

 

class product_category(models.Model):
    _inherit = "product.category" 

    code_saga = fields.Char(string="Code SAGA", size=2)
    

