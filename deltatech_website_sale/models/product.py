# -*- encoding: utf-8 -*-

 
from openerp import SUPERUSER_ID
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta

class product_template(models.Model):
 
    _inherit = 'product.template'

    # #008a00!important  - in stoc
    # #c45500!important  - la comanda  Usually dispatched within 4 to 5 days.
    

    is_qty_available = fields.Selection([('stock','In Stock'),('provider','In provider stock'),('order','At Order')], compute="_compute_available")
    at_order = fields.Boolean(string="Available at order")


    @api.multi
    def _compute_available(self):
        res = {}
        for product in self:
            if product.sudo().qty_available > 0:
                product.is_qty_available = 'stock'
            else:
                if product.at_order:
                    product.is_qty_available = 'order'
                else:
                    product.is_qty_available = 'provider'
        return res    
    _


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    def _default_website(self):
        return self.env['website'].search([], limit=1)

    website_id = fields.Many2one('website', string="website", default=_default_website)
    selectable = fields.Boolean(help="Allow the end user to choose this price list")
