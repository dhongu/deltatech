# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    def _default_confirmation_sms_sale_order_template(self):
        try:
            return self.env.ref('deltatech_sms_sale.sms_template_data_sale_order').id
        except ValueError:
            return False

    sale_order_sms_validation = fields.Boolean("SMS Confirmation", default=True)
    sale_sms_confirmation_template_id = fields.Many2one(
        'sms.template', string="SMS Template",
        domain="[('model', '=', 'sale.order')]",
        default=_default_confirmation_sms_sale_order_template,
        help="SMS sent to the customer once the sale order is confirmed.")
    has_received_warning_sale_sms = fields.Boolean()
