# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
#              Dan Stoica
# See README.rst file on addons root folder for license details

import logging

import requests

from odoo import api, models

_logger = logging.getLogger(__name__)


class SmsApi(models.AbstractModel):
    _inherit = "sms.api"

    @api.model
    def _contact_iap(self, local_endpoint, params):
        account = self.env["iap.account"].get("sms")


        res = []

        for message in params["messages"]:
            res_value = {"state": "success", "res_id": message["res_id"]}

            response = account.send_sms(message["number"], message["content"])

            if response['status'] != 200:
                res_value["state"] = "server_error"
                res_value["error"] = response['message']

            res += [res_value]

        return res
