# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class Website(models.Model):

    _inherit = "website"

    website_access_ids = fields.Many2many(
        "website",
        relation="website_access_rel",
        column2="website_id",
        column1="website_access_id",
        string="Access",
        help="Other websites from which the objects can be showed",
    )

    @api.model
    def website_domain(self, website_id=False):
        domain = super(Website, self).website_domain()
        if self.website_access_ids and not website_id:
            website_ids = [False] + self.website_access_ids.ids
            domain = [("website_id", "in", website_ids)]
        return domain
