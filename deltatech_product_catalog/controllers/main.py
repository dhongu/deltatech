# -*- coding: utf-8 -*-
# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import http
from odoo.http import request


class CataloguePrint(http.Controller):
    """This class includes the function which fetch the details
    about the corresponding product and print catalog in PDF format"""

    @http.route(['/report/pdf/catalog_download'], type='http', auth='public')
    def download_catalog(self, product_id):
        """In this function we are calling the report template
        of the corresponding product and
        downloads the catalog in pdf format"""
        pdf, _ = request.env.ref('deltatech_product_catalog.action_report_product_catalog')\
            .sudo().render_qweb_pdf([int(product_id)])
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf)),
                          ('Content-Disposition', 'catalog' + '.pdf;')]
        return request.make_response(pdf, headers=pdfhttpheaders)
