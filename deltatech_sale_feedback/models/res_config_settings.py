# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    days_request_feedback = fields.Integer(config_parameter="sale.days_request_feedback")
    sale_feedback = fields.Boolean(related="company_id.sale_feedback", readonly=False)
    sale_feedback_template_id = fields.Many2one(related="company_id.sale_feedback_template_id", readonly=False)
