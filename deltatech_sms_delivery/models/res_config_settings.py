# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    delivery_sms_preparation = fields.Boolean(
        related="company_id.delivery_sms_preparation", string="SMS Delivery Preparation", readonly=False
    )
    delivery_sms_preparation_template_id = fields.Many2one(
        related="company_id.delivery_sms_preparation_template_id", readonly=False
    )

    delivery_sms_ready = fields.Boolean(
        related="company_id.delivery_sms_ready", string="SMS Delivery Ready", readonly=False
    )
    delivery_sms_ready_template_id = fields.Many2one(
        related="company_id.delivery_sms_ready_template_id", readonly=False
    )
