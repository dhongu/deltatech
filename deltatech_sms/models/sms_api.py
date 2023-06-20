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
        # params['account_token'] = account.account_token
        # endpoint = self.env['ir.config_parameter'].sudo().get_param('sms.endpoint')

        res = []
        # endpoint = self.env["ir.config_parameter"].sudo().get_param("sms.endpoint", "")
        # endpoint =  account.endpoint or endpoint
        for message in params["messages"]:
            res_value = {"state": "success", "res_id": message["res_id"]}

            endpoint = account.endpoint
            if not endpoint:
                res_value["state"] = "Endpoint is not defined."
            endpoint = endpoint.format(**message)
            self.env.cr.execute("select unaccent(%s);", [endpoint])
            endpoint_unaccent = self.env.cr.fetchone()[0]
            result = requests.get(endpoint_unaccent)
            response = result.content.decode("utf-8")

            if "OK" not in response:
                _logger.error("SMS: %s" % response)
                res_value["state"] = "server_error"
            res += [res_value]

        return res
