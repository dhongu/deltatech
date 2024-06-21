# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models
from odoo.osv import expression
from odoo.tools import escape_psql
from odoo.tools.safe_eval import safe_eval


class WebsiteSearchableMixin(models.AbstractModel):
    """Mixin to be inherited by all models that need to searchable through website"""

    _inherit = "website.searchable.mixin"

    @api.model
    def _search_build_domain(self, domain_list, search, fields, extra=None):
        if search:
            get_param = self.env["ir.config_parameter"].sudo().get_param
            # cauta toata propozitia sau imparte in cuvinte
            full_sentence = safe_eval(get_param("alternative.full_sentence", "False"))
            if not full_sentence:
                search_term = search.strip().split(" ")
                min_len = safe_eval(get_param("alternative.length_min", "3"))
                search = " ".join(s.strip() for s in search_term if s.strip() and len(s.strip()) >= min_len)
            else:
                domains = domain_list.copy()
                subdomains = [[(field, "ilike", escape_psql(search))] for field in fields]
                if extra:
                    subdomains.append(extra(self.env, search))
                domains.append(expression.OR(subdomains))
                return expression.AND(domains)

        return super()._search_build_domain(domain_list, search, fields, extra)
