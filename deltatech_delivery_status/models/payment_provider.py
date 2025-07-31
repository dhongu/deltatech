# ©  2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class PaymentAcquirer(models.Model):
    _inherit = "payment.provider"

    postponed_delivery = fields.Boolean(
        string="Postponed Delivery",
        default=False,
        help="If enabled, the delivery will be postponed until the payment is confirmed.",
    )
