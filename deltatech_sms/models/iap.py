# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging

import requests
from unidecode import unidecode

from odoo import fields, models

_logger = logging.getLogger(__name__)


class IapAccount(models.Model):
    _inherit = "iap.account"

    # endpoint = fields.Char()

    sms_provider = fields.Selection(
        [("4pay", "SMS 4Pay"), ("wapi", "SMS Wapi")],
        string="SMS Provider",
    )
    sms_secret = fields.Char(string="SMS Secret")
    sms_gateway = fields.Char(string="SMS Gateway")

    def send_sms(self, phone_number, message):
        """Send SMS using IAP"""
        response = {}
        message = unidecode(message)  # Remove accents
        if self.sms_provider == "4pay":
            response = self._send_sms_4pay(phone_number, message)
        if self.sms_provider == "wapi":
            response = self._send_sms_wapi(phone_number, message)
        return response

    def _send_sms_4pay(self, phone_number, message):
        params = {
            "servID": self.sms_gateway,
            "msg_dst": phone_number,
            "msg_text": message,
            "API": "",
            "password": self.sms_secret,
            "external_messageID": 1,
        }
        result = requests.get("https://sms.4pay.ro/smscust/api.send_sms", params=params, timeout=60)
        response = result.content.decode("utf-8")

        if "OK" not in response:
            _logger.error(f"SMS: {response}")
            res = {"status": 500, "message": response, "data": False}
        else:
            res = {"status": 200, "message": "Message has been queued for sending!", "data": False}

        return res

    def _send_sms_wapi(self, phone_number, message):
        # Define the endpoint and payload
        url = "https://smswapi.com/api/send/sms"
        data = {
            "secret": self.sms_secret,
            "mode": "devices",
            "phone": phone_number,
            "message": message,
            "device": self.sms_gateway,
            "sim": 1,
        }

        # Make the POST request
        response = requests.post(url, data=data, timeout=60)

        res = response.json()
        _logger.info(f"SMS: {res}")

        if response.status_code == 200:
            res = response.json()
        else:
            res = {"status": 500, "message": response.content, "data": False}

        return res
