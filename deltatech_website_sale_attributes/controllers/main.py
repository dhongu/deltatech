from odoo import http
from odoo.http import request
from odoo.osv import expression

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleAttribute(WebsiteSale):
    @http.route()
    def shop(self, category=None, search="", **kwargs):
        # Only the two parameters this override actually reads are named; the
        # rest travels in ``kwargs`` untouched. The previous signature was
        # ``(page, category, search, ppg)`` and forwarded those positionally,
        # but core grew ``min_price``/``max_price`` in fourth and fifth place,
        # so ``ppg`` landed in ``min_price``: a visitor passing ``?ppg=40`` got
        # the catalogue silently filtered to products over 40 while the page
        # size stayed at its default. Odoo always invokes endpoints as
        # ``endpoint(**request.params)`` (``odoo/http.py``), so keyword
        # forwarding is both correct and immune to any further signature
        # change — including 19.0, where ``ppg`` became ``tags``.
        response = super().shop(category=category, search=search, **kwargs)

        if category and search:
            # Folosim domeniul construit de WebsiteSale pentru product.template
            website = request.env["website"].get_current_website()
            website_domain = website.website_domain()

            # Traducem domeniul pentru modelul product.template.attribute.value
            def _to_ptav(dom):
                res = []
                for term in dom:
                    if isinstance(term, list | tuple):
                        if len(term) == 3:
                            field, op, val = term
                            # Dacă e deja pe o cale, doar prefixăm cu product_tmpl_id.
                            if field.startswith("product_tmpl_id."):
                                res.append((field, op, val))
                            elif field == "id":
                                # Filtru direct pe ID-ul template-ului
                                res.append(("product_tmpl_id", op, val))
                            else:
                                res.append((f"product_tmpl_id.{field}", op, val))
                        else:
                            # termeni necanonici, lăsăm neschimbați
                            res.append(term)
                    else:
                        # operatori logici | & !
                        res.append(term)
                return res

            ptav_domain = expression.AND(
                [
                    _to_ptav(website_domain),
                    [("website_visible", "=", True)],
                ]
            )

            # Obținem valorile distincte prin read_group (evită materializarea tuturor produselor)
            groups = request.env["product.template.attribute.value"].read_group(
                domain=ptav_domain,
                fields=["product_attribute_value_id"],
                groupby=["product_attribute_value_id"],
                lazy=False,
            )
            value_ids = request.env["product.attribute.value"].browse(
                [g["product_attribute_value_id"][0] for g in groups if g.get("product_attribute_value_id")]
            )

            if category:
                # se ascund restul de categorii (păstrăm logica existentă)
                categories = response.qcontext.get("category")
                response.qcontext.update(categories=categories)
        else:
            domain = [("visibility", "=", "visible")]
            value_ids = request.env["product.attribute.value"].search(domain)

        response.qcontext.update(value_ids=value_ids)
        return response
