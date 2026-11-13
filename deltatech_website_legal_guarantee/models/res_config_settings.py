# © 2026 Deltatech
# See README.rst file on addons root folder for license details
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    legal_guarantee_footer = fields.Boolean(related="website_id.legal_guarantee_footer", readonly=False)
    legal_guarantee_product = fields.Boolean(related="website_id.legal_guarantee_product", readonly=False)
    legal_guarantee_checkout = fields.Boolean(related="website_id.legal_guarantee_checkout", readonly=False)
