# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
import requests


class SmsApi(models.AbstractModel):
    _inherit = 'sms.api'

    @api.model
    def _send_sms(self, numbers, message):
        """ Send sms
        """
        account = self.env['iap.account'].get('sms')

        params = {
            'username':account.user_name,
            'password': account.password,
            'to': numbers,
            'content': message,
        }
        endpoint = self.env['ir.config_parameter'].sudo().get_param('sms.endpoint', '')
        for number in numbers:
            params['to'] = number
            # result = requests.post(endpoint+'/send',params)
            result = requests.post(endpoint+'&recipients='+params['to']+'&sms='+params['content'])
            response = result.content.decode("utf-8")
            if 'Success' not in response:
                raise UserError('URL: '+result.url+'RESPONSE:'+response)

        return True


