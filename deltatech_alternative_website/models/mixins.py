# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models


class WebsiteSearchableMixin(models.AbstractModel):
    """Mixin to be inherited by all models that need to searchable through website"""

    _inherit = "website.searchable.mixin"

    @api.model
    def _search_build_domain(self, domain_list, search, fields, extra=None):
        if search:
            search = search.strip().split(" ")
            search = " ".join(s.strip() for s in search if s.strip())

        return super()._search_build_domain(domain_list, search, fields, extra)
