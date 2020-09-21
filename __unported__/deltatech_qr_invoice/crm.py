# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Deltatech All Rights Reserved
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


from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import   Warning, RedirectWarning
 

class account_invoice(models.Model):
    _name = "account.invoice"
    _inherit = ['account.invoice', 'crm.tracking.mixin']



class crm_tracking_campaign(models.Model):
    _inherit = "crm.tracking.campaign"

    short_text_qr = fields.Char(string='Short text QR')
    text_qr = fields.Char(string='Text QR')
    image_qr_html = fields.Html(string="QR image", compute="_compute_image_qr_html")

    @api.one
    def _compute_image_qr_html(self):
        self.image_qr_html = "<img src='/report/barcode/?type=%s&value=%s&width=%s&height=%s'/>" %   ('QR', self.text_qr, 100, 100)
        

    @api.multi
    def show_qr(self):
        
        #<img t-att-src="'/report/barcode/?type=%s&amp;value=%s&amp;width=%s&amp;height=%s' %   ('QR', o.name, 200, 200)"/>
        url =  '/report/barcode/?type=%s&value=%s&width=%s&height=%s' %   ('QR', self.text_qr, 200, 200)
        
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
            }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
