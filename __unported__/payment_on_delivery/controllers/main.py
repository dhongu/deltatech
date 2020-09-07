# -*- coding: utf-8 -*-
import logging
import pprint
import werkzeug

from odoo import http, SUPERUSER_ID
from odoo.http import request

_logger = logging.getLogger(__name__)


class OnDeliveryController(http.Controller):
    _accept_url = '/payment/on_delivery/feedback'

    @http.route([
        '/payment/on_delivery/feedback',
    ], type='http', auth='none')
    def on_delivery_form_feedback(self, **post):
        cr, uid, context = request.cr, SUPERUSER_ID, request.context
        _logger.info('Beginning form_feedback with post data %s', pprint.pformat(post))  # debug
        request.registry['payment.transaction'].form_feedback(cr, uid, post, 'on_delivery', context)
        return werkzeug.utils.redirect(post.pop('return_url', '/'))
