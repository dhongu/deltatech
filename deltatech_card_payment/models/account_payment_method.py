# ©  2015-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, models


class AccountPaymentMethod(models.Model):
    _inherit = "account.payment.method"

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res["card"] = {"mode": "unique", "domain": [("type", "=", "bank")]}
        return res
