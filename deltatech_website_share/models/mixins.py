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


class WebsitePublishedMultiMixin(models.AbstractModel):

    _inherit = "website.published.multi.mixin"

    def _compute_website_published(self):
        current_website_id = self._context.get("website_id")
        super(WebsitePublishedMultiMixin, self)._compute_website_published()
        for record in self:
            if current_website_id and record.website_id:
                record.website_published = record.is_published and (
                    record.website_id.id == current_website_id
                    or current_website_id in record.website_id.website_access_ids
                )
