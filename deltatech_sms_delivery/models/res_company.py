# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    def _default_sms_delivery_preparation_template(self):
        try:
            return self.env.ref("deltatech_sms_delivery.sms_template_delivery_preparation").id
        except ValueError:
            return False

    def _default_sms_delivery_ready_template(self):
        try:
            return self.env.ref("deltatech_sms_delivery.sms_template_delivery_ready").id
        except ValueError:
            return False

    delivery_sms_preparation = fields.Boolean("SMS Preparation", default=False)
    delivery_sms_preparation_template_id = fields.Many2one(
        "sms.template",
        string="SMS Template Delivery preparation",
        domain="[('model', '=', 'stock.picking')]",
        default=_default_sms_delivery_preparation_template,
        help="SMS sent to the customer once the delivery is in preparation.",
    )

    delivery_sms_ready = fields.Boolean("SMS Ready", default=False)
    delivery_sms_ready_template_id = fields.Many2one(
        "sms.template",
        string="SMS Template Delivery Confirmed",
        domain="[('model', '=', 'stock.picking')]",
        default=_default_sms_delivery_ready_template,
        help="SMS sent to the customer once the delivery is ready to pickup.",
    )
