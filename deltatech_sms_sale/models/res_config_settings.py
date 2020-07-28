# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_order_sms_validation = fields.Boolean(
        related='company_id.sale_order_sms_validation',
        string='SMS Validation with sale order', readonly=False)
    sale_sms_confirmation_template_id = fields.Many2one(
        related='company_id.sale_sms_confirmation_template_id', readonly=False)


