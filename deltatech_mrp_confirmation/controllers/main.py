# -*- coding: utf-8 -*-
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class BarcodeController(http.Controller):

    @http.route(['/barcode_mrp/web/'], type='http', auth='user')
    def a(self, debug=False, **k):
        if not request.session.uid:
            return http.local_redirect('/web/login?redirect=/barcode_mrp/web')

        return request.render('deltatech_mrp_confirmation.barcode_mrp_index')
