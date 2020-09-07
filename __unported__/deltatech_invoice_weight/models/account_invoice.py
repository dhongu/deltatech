# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _


class account_invoice(models.Model):
    _inherit = "account.invoice"

    weight = fields.Float('Gross Weight', digits='Stock Weight', help="The gross weight in Kg.")
    weight_net = fields.Float('Net Weight', digits='Stock Weight', help="The net weight in Kg.")
    weight_package = fields.Float('Package Weight', digits='Stock Weight')
