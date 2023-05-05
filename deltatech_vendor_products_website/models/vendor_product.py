# ©  2015-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class VendorProduct(models.Model):
    _name = "vendor.product"
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
            "search_fields": ["name", "code", "barcode"],
            "fetch_fields": ["name", "code", "url_image", "product_tmpl_id"],
            "mapping": {
                "name": {"name": "name", "type": "text", "match": True},
                "default_code": {"name": "code", "type": "text", "match": True},
                "website_url": {"name": "website_url", "type": "text", "truncate": False},
                "image_url": {"name": "image_url", "type": "html"},
            },
            "icon": "fa-tag",
            "order": "name asc, id desc",
        }

    def _search_render_results(self, fetch_fields, mapping, icon, limit):
        results_data = super()._search_render_results(fetch_fields, mapping, icon, limit)
        for data in results_data:
            data["website_url"] = "/vendor_product/%s" % data["id"]
            data["image_url"] = data["url_image"]
            if not data["name"]:
                data["name"] = data["code"]
            if data["product_tmpl_id"]:
                data["website_url"] = "/shop/product/%s" % data["product_tmpl_id"][0]
        return results_data
