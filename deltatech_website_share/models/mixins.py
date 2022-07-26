# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models
from odoo.http import request


class WebsiteMultiMixin(models.AbstractModel):
    _inherit = "website.multi.mixin"

    def can_access_from_current_website(self, website_id=False):
        can_access = super(WebsiteMultiMixin, self).can_access_from_current_website(website_id)
        if not can_access:
            for record in self:
                website_ids = [] or request.website.website_access_ids.ids
                if (website_id or record.website_id.id) in website_ids:
                    can_access = True
        return can_access
