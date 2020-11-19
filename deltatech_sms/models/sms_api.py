# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
#              Dan Stoica
# See README.rst file on addons root folder for license details

import logging

import requests

from odoo import api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SmsApi(models.AbstractModel):
    _inherit = "sms.api"

    @api.model
    def _send_sms(self, numbers, message):
        """ Send sms
        """
        account = self.env["iap.account"].get("sms")

        params = {
            "username": account.user_name,
            "password": account.password,
            "to": numbers,
            "content": message,
        }
        endpoint = self.env["ir.config_parameter"].sudo().get_param("sms.endpoint", "")
        for number in numbers:
            params["to"] = number
            # result = requests.post(endpoint+'/send',params)
            if account.user_name != "sms.4pay.ro":
                result = requests.get(endpoint + "&recipients=" + params["to"] + "&sms=" + params["content"])
            else:
                result = requests.get(endpoint + "&msg_dst=" + params["to"] + "&msg_text=" + params["content"])
            response = result.content.decode("utf-8")
            if "OK" not in response:
                raise UserError("URL: " + result.url + "RESPONSE:" + response)
            else:
                _logger.info("SMS sent: " + result.url)

        return True
