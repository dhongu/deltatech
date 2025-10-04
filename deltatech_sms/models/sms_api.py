# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
#              Dan Stoica
# See README.rst file on addons root folder for license details

import logging

from odoo.addons.sms.tools.sms_api import SmsApi as BaseSmsApi

_logger = logging.getLogger(__name__)


class SmsApi(BaseSmsApi):
    def _contact_iap(self, local_endpoint, params, timeout=15):
        account = self.env["iap.account"].get("sms")
        res = []
        for message in params["messages"]:
            for number in message["numbers"]:
                res_value = {"state": "success", "uuid": number["uuid"]}
                response = account.sudo().send_sms(number["number"], message["content"])
                if response["status"] != 200:
                    res_value["state"] = "server_error"
                    res_value["error"] = response["message"]
                res += [res_value]
        return res
