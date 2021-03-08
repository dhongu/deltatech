# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale as Base


class WebsiteSale(Base):
    @http.route("/shop/category/card", type="json", auth="public", website=True)
    def category_card(self, category_id=None, **kwargs):
        return self._get_category_card(category_id)

    def _get_category_card(self, category_id=None):
        """
        Returns list of  categories according to snippet settings
        """
        Category = request.env["product.public.category"]
        category_list = Category.sudo().browse(category_id)
        if not category_list:
            return {}

        res = {"categories": []}
        for category in category_list.child_id:
            res_category = {
                "id": category.id,
                "name": category.name,
                "website_url": category.website_url,
            }

            res["categories"].append(res_category)

        return res
