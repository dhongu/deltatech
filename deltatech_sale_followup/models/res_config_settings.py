# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sale_followup = fields.Boolean(related="company_id.sale_followup", readonly=False)
    sale_followup_template_id = fields.Many2one(related="company_id.sale_followup_template_id", readonly=False)
