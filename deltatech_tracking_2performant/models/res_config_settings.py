# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    @api.depends("website_id")
    def _compute_has_2performant(self):
        for item in self:
            item.has_2performant = bool(item.campaign_unique_2p)

    def _inverse_has_2performant(self):
        if not self.has_2performant:
            self.campaign_unique_2p = False
            self.confirm_2p = False

    campaign_unique_2p = fields.Char(related="company_id.campaign_unique_2p", readonly=False)
    confirm_2p = fields.Char(related="company_id.confirm_2p", readonly=False)
    has_2performant = fields.Boolean(
        string="2Performant tracking", compute=_compute_has_2performant, inverse=_inverse_has_2performant
    )
