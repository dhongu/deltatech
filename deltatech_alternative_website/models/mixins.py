# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models
from odoo.tools.safe_eval import safe_eval


class WebsiteSearchableMixin(models.AbstractModel):
    """Mixin to be inherited by all models that need to searchable through website"""

    _inherit = "website.searchable.mixin"

    @api.model
    def _search_build_domain(self, domain_list, search, fields, extra=None):
        if search:
            get_param = self.env["ir.config_parameter"].sudo().get_param
            search = search.strip().split(" ")
            min_len = safe_eval(get_param("alternative.length_min", "3"))
            search = " ".join(s.strip() for s in search if s.strip() and len(s.strip()) > min_len)

        return super()._search_build_domain(domain_list, search, fields, extra)
