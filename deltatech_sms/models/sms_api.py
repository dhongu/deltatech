# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
#              Dan Stoica
# See README.rst file on addons root folder for license details

import logging

import requests

from odoo.addons.sms.tools.sms_api import SmsApi as BaseSmsApi

_logger = logging.getLogger(__name__)


class SmsApi(BaseSmsApi):
    def _contact_iap(self, local_endpoint, params, timeout=15):
        account = self.env["iap.account"].get("sms")

        res = []

        for message in params["messages"]:
            res_value = {"state": "success"}

            endpoint = account.endpoint
            if not endpoint:
                res_value["state"] = "Endpoint is not defined."

            for number in message["numbers"]:
                res_value["uuid"] = number["uuid"]
                endpoint_number = endpoint.format(number=number["number"], content=message["content"])
                self.env.cr.execute("select unaccent(%s);", [endpoint_number])
                endpoint_unaccent = self.env.cr.fetchone()[0]
                result = requests.get(endpoint_unaccent, timeout=60)
                response = result.content.decode("utf-8")

                if "OK" not in response:
                    _logger.error(f"SMS: {response}")
                    res_value["state"] = "server_error"
                res += [res_value]

        return res
