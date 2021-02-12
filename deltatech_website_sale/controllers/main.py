# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2017 Deltatech All Rights Reserved
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
#
##############################################################################

import babel.dates
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import werkzeug.urls
from werkzeug.exceptions import NotFound

from openerp import http
from openerp import tools
from openerp.http import request
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug

from openerp import SUPERUSER_ID

from openerp.addons.website_sale.controllers.main import website_sale
from openerp.addons.website_sale.controllers.main import QueryURL


class WebsiteSale(website_sale):
    def get_pricelist(self):
        return request.website.get_current_pricelist()


class website_stock(http.Controller):
    @http.route(['/stock/products', '/stock/products/page/<int:page>'], type='http', auth="user", website=True)
    def products(self, page=1, search='', **post):
        cr, uid, context = request.cr, request.uid, request.context
        product_obj = request.registry['product.product']

        step = 10  # Number of products per page
        order = 'name'

        domain = []
        if search:
            for srch in search.split(" "):
                domain += ['|',
                           ('name', 'ilike', srch),
                           ('default_code', 'ilike', srch), ]

        product_count = product_obj.search(request.cr, request.uid, domain, count=True, context=request.context)

        pager = request.website.pager(url="/stock/products", url_args={},
                                      total=product_count, page=page, step=step, scope=5)

        obj_ids = product_obj.search(request.cr, request.uid, domain, limit=step,
                                     offset=pager['offset'], order=order, context=request.context)

        product_ids = product_obj.browse(request.cr, request.uid, obj_ids, context=request.context)

        values = {
            'search': search,
            'product_ids': product_ids,
            'pager': pager,

        }

        return request.website.render("deltatech_website_sale.products", values)

    @http.route(['/stock/product/<model("product.product"):product>'], type='http', auth="user", website=True)
    def product_page(self, product, search='', message='', message_type='', **post):

        values = {
            'search': search,
            'product': product,
        }
        # alert-success 
        return request.website.render("deltatech_website_sale.product", values)

    @http.route(['/shop/change_pricelist/<model("product.pricelist"):pl_id>'], type='http', auth="public", website=True)
    def pricelist_change(self, pl_id, **post):
        if (pl_id.selectable or pl_id == request.env.user.partner_id.property_product_pricelist) \
                and request.website.is_pricelist_available(pl_id.id):
            request.session['website_sale_current_pl'] = pl_id.id
            # request.website.sale_get_order(force_pricelist=pl_id.id)
        return request.redirect(request.httprequest.referrer or '/shop')

    @http.route(['/shop/pricelist'], type='http', auth="public", website=True)
    def pricelist(self, promo, **post):
        pricelist = request.env['product.pricelist'].sudo().search([('code', '=', promo)], limit=1)
        if pricelist and not request.website.is_pricelist_available(pricelist.id):
            return request.redirect("/shop/cart?code_not_available=1")

        request.website.sale_get_order(code=promo)
        return request.redirect("/shop/cart")
