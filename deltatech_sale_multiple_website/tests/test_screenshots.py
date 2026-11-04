# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Cantitate minimă și multiplă în magazinul online" — generate
# în timpul testelor, în limba RO (fișa) și EN (readme/USAGE.md).
#
# Fluxul: regulile pe produs (Cantitate multiplă, Cantitate minimă, Verifică cantitatea pe
# website), restricțiile afișate pe pagina produsului din magazin, coșul cu cantitatea rotunjită
# și o comandă din backend pe care regula „doar pe website" nu se aplică.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_sale_multiple_website,deltatech_doc_screenshots \
#       --test-tags=/deltatech_sale_multiple_website:TestSaleMultipleWebsiteScreenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# după încărcarea paginii (interacțiunile magazinului), deschide explicația regulii de multiplu
OPEN_POPOVER_JS = """async () => {
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    await sleep(2000);
    // explicația sub restricții, ca să nu acopere butonul de adăugare în coș
    const button = document.querySelector("#product_qty_restrictions .qty-multiple-rule .qty-info-popover");
    window.Popover.getInstance(button)?.dispose();
    button.setAttribute("data-bs-placement", "bottom");
    window.Popover.getOrCreateInstance(button);
    button.focus();
    await sleep(1000);
}"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestSaleMultipleWebsiteScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_sale_multiple_website"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company()
        cls.website = cls.env["website"].get_current_website()
        # magazinul în română, cu engleza ca a doua limbă (capturile EN pentru USAGE.md)
        lang_ro = cls.env.ref("base.lang_ro")
        lang_en = cls.env.ref("base.lang_en")
        cls.website.write(
            {
                "name": "Magazin Demo Feronerie",
                "language_ids": [Command.set((lang_ro | lang_en).ids)],
                "default_lang_id": lang_ro.id,
            }
        )
        # prețuri în RON, fără reducerile listelor de prețuri demo, și TVA 21%
        # (pe baza demo, moneda companiei rămâne USD: prețurile se afișează în RON prin listă, la curs 1)
        company = cls.env.company
        ron = cls.env.ref("base.RON")
        ron.active = True
        ron.rate_ids.unlink()
        cls.env["res.currency.rate"].create({"currency_id": ron.id, "rate": 1.0, "company_id": company.id})
        pricelists = cls.env["product.pricelist"].search([])
        pricelist = cls.env["product.pricelist"].create(
            {"name": "Listă de prețuri publică", "currency_id": ron.id, "company_id": company.id}
        )
        pricelists.active = False
        cls.env["res.partner"].search([]).property_product_pricelist = pricelist
        # fără nota de termeni cu adresa serverului de test în subsolul ofertei
        company.terms_type = "plain"
        company.invoice_terms = False
        country = company.account_fiscal_country_id
        tax_group = cls.env["account.tax.group"].create(
            {"name": "TVA 21%", "company_id": company.id, "country_id": country.id}
        )
        vat_21 = cls.env["account.tax"].create(
            {
                "name": "TVA 21%",
                "amount": 21.0,
                "type_tax_use": "sale",
                "company_id": company.id,
                "country_id": country.id,
                "tax_group_id": tax_group.id,
            }
        )
        category = cls.env["product.public.category"].create({"name": "Feronerie"})
        category.update_field_translations("name", {"ro_RO": "Feronerie", "en_US": "Hardware"})
        # produs vândut doar în pachete de 50 bucăți, minimum 100 bucăți pe comanda din magazin
        cls.product = cls.env["product.template"].create(
            {
                "name": "Șurub autoforant 4,2 x 13 mm",
                "default_code": "SRB-4213",
                "type": "consu",
                "list_price": 0.35,
                "sale_ok": True,
                "is_published": True,
                "website_id": cls.website.id,
                "public_categ_ids": [Command.set(category.ids)],
                "check_min_website": True,
                "taxes_id": [Command.set(vat_21.ids)],
            }
        )
        cls.product.update_field_translations(
            "name", {"ro_RO": "Șurub autoforant 4,2 x 13 mm", "en_US": "Self-drilling screw 4.2 x 13 mm"}
        )
        variant = cls.product.product_variant_id
        variant.write({"qty_multiple": 50.0, "qty_minim": 100.0})
        admin_partner = cls.env.ref("base.user_admin").partner_id
        # coșul (abandonat) al utilizatorului care face capturile: 130 bucăți cerute,
        # rotunjite la multiplul următor, 150
        cls.cart = cls.env["sale.order"].create(
            {
                "partner_id": admin_partner.id,
                "website_id": cls.website.id,
                "order_line": [Command.create({"product_id": variant.id, "product_uom_qty": 130.0})],
            }
        )
        # o ofertă din backend: regula e doar pentru website, cantitatea rămâne 130
        customer = cls.env["res.partner"].create(
            {"name": "Construct Montaj SRL", "is_company": True, "city": "Cluj-Napoca"}
        )
        cls.quotation = cls.env["sale.order"].create(
            {
                "partner_id": customer.id,
                "order_line": [Command.create({"product_id": variant.id, "product_uom_qty": 130.0})],
            }
        )
        cls.env.flush_all()
        assert cls.cart.order_line.product_uom_qty == 150.0, cls.cart.order_line.product_uom_qty
        assert cls.quotation.order_line.product_uom_qty == 130.0, cls.quotation.order_line.product_uom_qty

    def _shots(self):
        sales_tab = {"ro_RO": "Vânzări", "en_US": "Sales"}
        product_form = f"id={self.product.id}&model=product.template&view_type=form"
        quotation_form = f"id={self.quotation.id}&model=sale.order&view_type=form"
        product_path = self.product.website_url
        return [
            # 1. regulile pe produs: multiplu, minim și „doar pe website"
            {
                "url": product_form,
                "name": "01_reguli_cantitate_produs.png",
                "wait": ".o_form_view",
                "click_tab": sales_tab,
                "highlight": [
                    "div[name='qty_multiple']",
                    "div[name='qty_minim']",
                    "div[name='check_min_website']",
                ],
            },
            # 2. pagina produsului din magazin: restricțiile și explicația multiplului
            {
                "path": {"ro_RO": product_path, "en_US": f"/en{product_path}"},
                "name": "02_restrictii_pagina_produs.png",
                "wait": "#product_detail",
                "eval": OPEN_POPOVER_JS,
                "eval_wait": 1000,
                "settle": 2000,
                "highlight": ["#product_qty_restrictions"],
            },
            # 3. coșul: 130 bucăți cerute au devenit 150, regulile sunt amintite sub produs
            {
                "path": {"ro_RO": "/shop/cart", "en_US": "/en/shop/cart"},
                "name": "03_cos_cantitate_rotunjita.png",
                "wait": "#cart_products",
                "settle": 2500,
                "highlight": [
                    "#cart_products .text-muted.small:has(.fa-th-large)",
                    "#cart_products .css_quantity",
                ],
            },
            # 4. oferta din backend: regula „doar pe website" nu se aplică, cantitatea rămâne 130
            {
                "url": quotation_form,
                "name": "04_oferta_backend_fara_regula.png",
                "wait": ".o_form_view",
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), viewport=(1920, 1100), hide_systray=True)

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), viewport=(1920, 1100), hide_systray=True, lang="en_US")
