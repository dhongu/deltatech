# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Prețurile de vânzare într-o altă monedă decât moneda companiei"
# — generate în timpul testelor, în limba RO (fișa) și EN (readme/USAGE.md).
#
# Fluxul: compania în RON are Moneda listei de prețuri EUR, cursul EUR, produsul cu prețul de
# vânzare în EUR și costul în RON, apoi comanda de vânzare în RON cu prețul convertit la curs.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_pricelist,deltatech_doc_screenshots \
#       --test-tags=/deltatech_pricelist:TestPricelistScreenshots --stop-after-init
import json
import unittest
from datetime import timedelta

from odoo import Command, fields
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

EUR_RATE = 5.0  # 1 EUR = 5 RON, curs rotund ca valorile din capturi să se verifice ușor
LIST_PRICE_EUR = 120.0
COST_RON = 400.0

# bulinele numerotate ies din chenarul câmpului; containerele cu overflow ascuns le-ar tăia
UNCLIP_JS = """(selectors) => {
    for (const sel of selectors) {
        for (const el of document.querySelectorAll(sel)) {
            for (let node = el; node && node !== document.body; node = node.parentElement) {
                node.style.overflow = "visible";
            }
        }
    }
}"""


def _unclip(*selectors):
    return "() => (" + UNCLIP_JS + ")(" + json.dumps(list(selectors)) + ")"


@tagged("-at_install", "post_install", "fise_screenshots")
class TestPricelistScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_pricelist"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.company = cls.prepare_ro_company()
        env = cls.env
        eur = env.ref("base.EUR")
        ron = env.ref("base.RON")
        eur.active = True
        # admin vede monedele și listele de prețuri (coloanele și câmpurile multi-monedă)
        admin = env.ref("base.user_admin")
        for xmlid in ("base.group_multi_currency", "product.group_product_pricelist"):
            admin.group_ids = [Command.link(env.ref(xmlid).id)]
        # setarea modulului: prețurile de vânzare ale companiei sunt în EUR
        cls.company.price_currency_id = eur
        # un singur curs EUR, al companiei în RON; în 20 cursul se aplică din ziua următoare datei lui,
        # deci îl punem pe ieri ca să intre pe comanda de azi
        env["res.currency.rate"].search([("currency_id", "in", (eur | ron).ids)]).unlink()
        env["res.currency.rate"].create(
            {
                "name": fields.Date.today() - timedelta(days=1),
                "currency_id": eur.id,
                "company_id": cls.company.id,
                "inverse_company_rate": EUR_RATE,
            }
        )
        cls.eur = eur
        # TVA 21% în locul taxei generice a planului de conturi implicit
        tax_group = env["account.tax.group"].create({"name": "TVA 21%", "company_id": cls.company.id})
        tax = env["account.tax"].create(
            {
                "name": "TVA 21%",
                "amount": 21.0,
                "type_tax_use": "sale",
                "tax_group_id": tax_group.id,
                "company_id": cls.company.id,
            }
        )
        cls.product = env["product.template"].create(
            {
                "name": "Pompă submersibilă 750 W",
                "default_code": "PMP-750",
                "type": "consu",
                "sale_ok": True,
                "list_price": LIST_PRICE_EUR,
                "standard_price": COST_RON,
                "company_id": cls.company.id,
                "taxes_id": [Command.set(tax.ids)],
                "supplier_taxes_id": [Command.clear()],
            }
        )
        cls.product.update_field_translations(
            "name", {"ro_RO": "Pompă submersibilă 750 W", "en_US": "Submersible pump 750 W"}
        )
        pricelist = env["product.pricelist"].create(
            {"name": "Prețuri RON", "currency_id": ron.id, "company_id": cls.company.id}
        )
        pricelist.update_field_translations("name", {"ro_RO": "Prețuri RON", "en_US": "RON prices"})
        partner = env["res.partner"].create({"name": "Client Demo SRL"})
        cls.order = env["sale.order"].create(
            {
                "partner_id": partner.id,
                "pricelist_id": pricelist.id,
                "company_id": cls.company.id,
                "order_line": [Command.create({"product_id": cls.product.product_variant_id.id, "product_uom_qty": 2})],
            }
        )
        env.flush_all()

    def _shots(self):
        return [
            # 1. setarea modulului pe companie
            {
                "url": f"id={self.company.id}&model=res.company&view_type=form",
                "name": "01_moneda_lista_preturi_companie.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='currency_id']", "div[name='price_currency_id']"],
            },
            # 2. cursul EUR folosit la conversie
            {
                "url": f"id={self.eur.id}&model=res.currency&view_type=form",
                "name": "02_curs_eur.png",
                "wait": ".o_form_view",
                "eval": _unclip("div[name='rate_ids'] .o_data_row"),
                "highlight": ["div[name='rate_ids'] .o_data_row"],
            },
            # 3. produsul: prețul de vânzare în EUR, costul în RON
            {
                "url": f"id={self.product.id}&model=product.template&view_type=form",
                "name": "03_pret_vanzare_eur_produs.png",
                "wait": ".o_form_view",
                "eval": _unclip("div[name='list_price']", "div[name='standard_price']"),
                "highlight": ["div[name='list_price_uom']", "div[name='standard_price_uom']"],
            },
            # 4. comanda în RON: prețul unitar convertit la curs
            {
                "url": f"id={self.order.id}&model=sale.order&view_type=form",
                "name": "04_comanda_vanzare_pret_ron.png",
                "wait": ".o_form_view",
                "eval": _unclip(".o_data_row td[name='price_unit']"),
                "highlight": ["div[name='pricelist_id']", ".o_data_row td[name='price_unit']"],
            },
        ]

    def test_capture_fise(self):
        line = self.order.order_line
        # prețul de vânzare de 120 EUR ajunge pe comanda în RON la cursul de 5 RON/EUR
        self.assertEqual(self.product.currency_id, self.eur)
        self.assertEqual(self.product.cost_currency_id, self.company.currency_id)
        self.assertAlmostEqual(line.price_unit, LIST_PRICE_EUR * EUR_RATE, places=2)
        # lista în EUR nu convertește; discountul de 10% pe lista în RON se aplică după conversie
        product = self.product.product_variant_id
        pricelist = self.env["product.pricelist"]
        eur_list = pricelist.create({"name": "EUR", "currency_id": self.eur.id, "company_id": self.company.id})
        self.assertAlmostEqual(eur_list._get_product_price(product, 1.0), LIST_PRICE_EUR, places=2)
        discount_list = pricelist.create(
            {
                "name": "RON -10%",
                "currency_id": self.company.currency_id.id,
                "company_id": self.company.id,
                "item_ids": [Command.create({"compute_price": "discount", "price_discount": 10.0})],
            }
        )
        self.assertAlmostEqual(discount_list._get_product_price(product, 1.0), 540.0, places=2)
        self.capture_screenshots(self._shots(), viewport=(1920, 1000), hide_systray=True)

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), viewport=(1920, 1000), hide_systray=True, lang="en_US")
