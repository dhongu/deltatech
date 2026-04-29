from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleAttributeFilter(WebsiteSale):
    def shop(self, page=0, category=None, search="", min_price=0.0, max_price=0.0, ppg=False, **post):
        response = super().shop(
            page=page, category=category, search=search, min_price=min_price, max_price=max_price, ppg=ppg, **post
        )
        if not hasattr(response, "qcontext") or not response.qcontext:
            return response

        # Initialize to avoid errors in templates if not set
        response.qcontext.setdefault("active_attribute_value_ids", set())

        search_product = response.qcontext.get("search_product")
        if search_product:
            # Găsim toate valorile de atribute utilizate în produsele găsite
            # Folosim product.template.attribute.line pentru a găsi valorile corecte (mai eficient)
            ptals = (
                request.env["product.template.attribute.line"]
                .sudo()
                .search([("product_tmpl_id", "in", search_product.ids)])
            )
            active_value_ids = ptals.mapped("value_ids").ids
            response.qcontext.update(active_attribute_value_ids=set(active_value_ids))

        # print("DEBUG: active_attribute_value_ids", response.qcontext.get("active_attribute_value_ids"))

        # Adăugăm active_attribute_value_ids la cache key dacă e nevoie,
        # dar mai bine am dezactivat cache-ul în template-uri pentru simplitate.

        return response
