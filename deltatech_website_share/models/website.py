# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class Website(models.Model):

    _inherit = "website"

    website_access_ids = fields.Many2many(
        "website", relation="website_access_rel", column2="website_id", column1="website_access_id", string="Access"
    )

    @api.model
    def website_domain(self, website_id=False):
        website_ids = self.website_access_ids.ids or []
        website_ids += [False, website_id or self.id]
        return [("website_id", "in", website_ids)]
