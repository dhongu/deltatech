# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    use_company_email = fields.Boolean(string="Use Company Email", config_parameter='mail.use_company_email')
