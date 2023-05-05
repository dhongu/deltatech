# ©  2015-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class VendorProduct(models.Model):
    _inherit = [
        "vendor.product",
        "website.published.mixin",
        "website.searchable.mixin",
    ]

    @api.model
    def _search_get_detail(self, website, order, options):
        return {
            "model": "vendor.product",
            "base_domain": [],
            "search_fields": ["name", "code"],
            "fetch_fields": ["name", "code"],
            "mapping": {
                "name": {"name": "name", "type": "text", "match": True},
                "website_url": {"name": "name", "type": "text", "truncate": False},
            },
            "icon": "fa-check-square-o",
            "order": "name asc, id desc",
        }
