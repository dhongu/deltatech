# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Producătorul, dimensiunile și termenul de valabilitate ale
# produsului" — generate în timpul testelor, în limba RO, pe compania „Demo Alimentare SRL" în RON.
#
# Seed: doi producători (Carpați Lactate SRL, Livada Mureș SRL) și un furnizor care nu e
# producător (Logistic Expres SRL). Trei produse cu producător, dimensiuni și valabilitate în
# zile, vândute pe trei facturi client postate în luna curentă:
#   - Iaurt natural 1 kg: 40 × 12 lei = 480 lei (Carpați Lactate);
#   - Telemea de vacă 500 g: 25 × 24 lei = 600 lei (Carpați Lactate);
#   - Mere Golden 1 kg: 60 × 9 lei = 540 lei (Livada Mureș).
# Alimentele au TVA 11 % (cota redusă), nu cota implicită a companiei.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i l10n_ro,l10n_ro_doc_screenshots -u deltatech_product_extension \
#       --test-tags=fise_screenshots/deltatech_product_extension --stop-after-init
import unittest

from dateutil.relativedelta import relativedelta

from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestProductExtensionScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_product_extension"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Alimentare SRL")
        company = cls.company = cls.env.company
        cls.env = cls.env(context=dict(cls.env.context, allowed_company_ids=company.ids, lang="ro_RO"))
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        (admin | env.user).tz = "Europe/Bucharest"
        for xmlid in ["account.group_account_invoice", "account.group_account_readonly"]:
            admin.group_ids = [Command.link(env.ref(xmlid).id)]

        # baza poate avea produse demo: le arhivăm, ca listele să arate doar produsele fluxului
        env["product.template"].sudo().search([]).active = False

        # câmpul american „1099 Box" (l10n_us_1099, dacă e instalat) ar sta chiar deasupra bifei
        us_1099_view = env.ref("l10n_us_1099.view_partner_property_form", raise_if_not_found=False)
        if us_1099_view:
            us_1099_view.active = False

        ro = env.ref("base.ro")

        def partner(name, city, street, manufacturer, vat=False):
            return env["res.partner"].create(
                {
                    "name": name,
                    "is_company": True,
                    "vat": vat,
                    "country_id": ro.id,
                    "city": city,
                    "street": street,
                    "is_manufacturer": manufacturer,
                }
            )

        cls.carpati = partner("Carpați Lactate SRL", "Brașov", "Str. Zizinului nr. 110", True)
        cls.livada = partner("Livada Mureș SRL", "Târgu Mureș", "Str. Gheorghe Doja nr. 64", True)
        cls.logistic = partner("Logistic Expres SRL", "Ploiești", "Str. Depoului nr. 5", False)
        cls.customer = partner("Market Central SRL", "București", "Bd. Unirii nr. 20", False, vat="RO18547290")

        cls.categ = env["product.category"].create({"name": "Alimentare"})
        day = env.ref("uom.product_uom_day")

        def tax(use):
            return env["account.tax"].search(
                [("company_id", "=", company.id), ("type_tax_use", "=", use), ("name", "=", "11% G")], limit=1
            )

        sale_tax, purchase_tax = tax("sale"), tax("purchase")
        assert sale_tax and purchase_tax, "lipsește TVA 11% G din planul RO"
        # lista de prețuri a fixture-ului apare pe partener; îi dăm un nume de firmă reală
        env["product.pricelist"].search([("name", "=like", "Test Pricelist%")]).name = "Listă de prețuri standard"

        def product(name, manufacturer, dimensions, shelf_life, cost, price):
            return env["product.product"].create(
                {
                    "name": name,
                    "type": "consu",
                    "categ_id": cls.categ.id,
                    "manufacturer_id": manufacturer.id,
                    "dimensions": dimensions,
                    "shelf_life": shelf_life,
                    "uom_shelf_life": day.id,
                    "standard_price": cost,
                    "list_price": price,
                    "company_id": cls.company.id,
                    "taxes_id": [Command.set(sale_tax.ids)],
                    "supplier_taxes_id": [Command.set(purchase_tax.ids)],
                }
            )

        cls.yogurt = product("Iaurt natural 1 kg", cls.carpati, "12 x 12 x 10 cm", 21, 8.5, 12.0)
        cls.cheese = product("Telemea de vacă 500 g", cls.carpati, "15 x 10 x 6 cm", 60, 17.0, 24.0)
        cls.apples = product("Mere Golden 1 kg", cls.livada, "25 x 15 x 8 cm", 30, 6.0, 9.0)

        today = fields.Date.context_today(env["res.partner"])
        invoice_date = max(today.replace(day=1), today - relativedelta(days=5))
        for prod, qty in ((cls.yogurt, 40), (cls.cheese, 25), (cls.apples, 60)):
            invoice = env["account.move"].create(
                {
                    "move_type": "out_invoice",
                    "partner_id": cls.customer.id,
                    "invoice_date": invoice_date,
                    "invoice_line_ids": [
                        Command.create({"product_id": prod.id, "quantity": qty, "price_unit": prod.list_price})
                    ],
                }
            )
            invoice.action_post()

        cls.act_partners = env.ref("account.res_partner_action_customer")
        cls.act_products = env.ref("account.product_product_action_sellable")
        cls.act_analysis = env.ref("account.action_account_invoice_report_all")
        # aceeași acțiune, deschisă direct pe pivotul grupat după producător (ca după alegerea
        # „Grupează după > Producător" din căutare)
        cls.act_analysis_manufacturer = cls.act_analysis.copy(
            {
                "path": False,
                "context": "{'search_default_current': 1, 'search_default_customer': 1, "
                "'search_default_group_manufacturer': 1}",
            }
        )

    def _capture(self, shots):
        self.env.flush_all()
        self.capture_screenshots(shots, hide_systray=True)

    def test_capture_fise(self):
        product_url = (
            f"action={self.act_products.id}&id={self.yogurt.product_tmpl_id.id}&model=product.template&view_type=form"
        )
        self._capture(
            [
                {
                    "url": f"action={self.act_partners.id}&id={self.carpati.id}&model=res.partner&view_type=form",
                    "name": "01_partener_producator.png",
                    "wait": ".o_form_view",
                    "click_tab": "Vânzări & Achiziții",
                    "settle": 2000,
                    "highlight": ["div[name='is_manufacturer']"],
                },
                {
                    "url": product_url,
                    "name": "02_produs_producator.png",
                    "wait": ".o_form_view",
                    "settle": 2000,
                    "highlight": [
                        "div[name='manufacturer_id']",
                        "div[name='dimensions']",
                        "div:has(> div[name='uom_shelf_life'])",
                    ],
                },
                {
                    "url": product_url,
                    "name": "03_alegere_producator.png",
                    "wait": ".o_form_view",
                    "click_btn": "div[name='manufacturer_id'] input",
                    "wait_after": ".o-autocomplete--dropdown-menu",
                    "settle": 2000,
                },
                {
                    "url": f"action={self.act_analysis.id}&view_type=pivot",
                    "name": "04_analiza_facturi_grupare.png",
                    "wait": ".o_pivot",
                    "click_btn": ".o_searchview_dropdown_toggler",
                    "wait_after": ".o_group_by_menu",
                    "settle": 2000,
                    "highlight": [".o_group_by_menu .o-dropdown-item:has-text('Producător')"],
                },
                {
                    "url": f"action={self.act_analysis_manufacturer.id}&view_type=pivot",
                    "name": "05_analiza_facturi_producator.png",
                    "wait": ".o_pivot",
                    "settle": 2500,
                },
            ]
        )
