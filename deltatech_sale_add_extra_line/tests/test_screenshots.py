# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Linie suplimentară automată pe comanda de vânzare" — generate
# în timpul testelor, în limba RO, pe compania „RO Company" în RON.
#
# Seedează două scenarii comerciale:
#   * centrală termică + serviciu de montaj la 10% din preț (Extra Percent) — pașii 1, 2, 4, 5, 6;
#   * bax de bere + garanție de ambalaj 0,50 RON, 6 bucăți per bax (Extra Qty) — pasul 3.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_sale_add_extra_line,l10n_ro,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestSaleAddExtraLineScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_sale_add_extra_line"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Vânzări SRL")  # RON, drepturi contabile + limba RO
        company = cls.env.company
        cls.env.ref("base.user_admin").write({"company_ids": [(4, company.id)], "company_id": company.id})

        env = cls.env
        # drepturi de vânzări: pe utilizatorul testului (ca să poată seeda comenzile) și pe admin
        # (care e cel autentificat în browserul de capturi)
        sale_manager = env.ref("sales_team.group_sale_manager", raise_if_not_found=False)
        if sale_manager:
            env.user.group_ids = [Command.link(sale_manager.id)]
            env.ref("base.user_admin").group_ids = [Command.link(sale_manager.id)]
            env.flush_all()

        cls.partner = env["res.partner"].create({"name": "Instal Prest SRL", "country_id": env.ref("base.ro").id})
        # denumire de listă de prețuri prezentabilă în manual (fixture-ul de test se numește
        # „Test Pricelist", care nu are ce căuta într-o captură de documentație)
        cls.partner.property_product_pricelist.name = "Listă de prețuri clienți RON"

        # Scenariul 1 — serviciu de montaj facturat ca procent din valoarea echipamentului
        cls.service = env["product.product"].create(
            {"name": "Serviciu montaj și punere în funcțiune", "type": "service", "list_price": 400.0}
        )
        cls.boiler = env["product.product"].create(
            {
                "name": "Centrală termică 24 kW",
                "type": "consu",
                "list_price": 4500.0,
                "extra_product_id": cls.service.id,
                "extra_percent": 10.0,
                "extra_qty": 1.0,
            }
        )

        # Scenariul 2 — ambalaj cu preț propriu, 6 bucăți per bax (multiplicator). Deliberat un
        # ambalaj nereturnabil vândut cu TVA, nu o garanție SGR: garanția SGR este în afara sferei
        # TVA (art. 315^5 alin. 2 Cod fiscal), deci nu poate ilustra un exemplu cu TVA 21%.
        cls.packaging = env["product.product"].create(
            {"name": "Ambalaj carton nereturnabil", "type": "consu", "list_price": 0.5}
        )
        cls.beer_box = env["product.product"].create(
            {
                "name": "Bax bere blondă 6 × 0,5 L",
                "type": "consu",
                "list_price": 42.0,
                "extra_product_id": cls.packaging.id,
                "extra_percent": 0.0,
                "extra_qty": 6.0,
            }
        )

        # Pasul 2 — comandă cu linia extra generată automat (2 centrale → 2 montaje la 450 RON)
        cls.so_auto = cls._make_order(cls.boiler, 2)

        # Pasul 3 — cantitatea urmează linia principală prin multiplicator (10 baxuri → 60 garanții)
        cls.so_qty = cls._make_order(cls.beer_box, 10)

        # Pasul 4 — preț negociat manual pe linia extra, păstrat la modificarea liniei principale
        cls.so_manual = cls._make_order(cls.boiler, 2)
        extra_manual = cls._extra_line_of(cls.so_manual, cls.service)
        extra_manual.price_unit = 300.0
        cls.so_manual.order_line.filtered(lambda li: li.product_id == cls.boiler).product_uom_qty = 3
        cls.so_manual.order_line.check_extra_product()

        # Pasul 5 — după ștergerea liniei extra, aceasta se regenerează cu prețul calculat
        cls.so_reset = cls._make_order(cls.boiler, 2)
        extra_reset = cls._extra_line_of(cls.so_reset, cls.service)
        extra_reset.price_unit = 300.0
        extra_reset.unlink()
        cls.so_reset.order_line.check_extra_product()

        # Pasul 6 — factura ciornă care preia linia extra din comandă. Comandă proprie: cea de la
        # pasul 2 trebuie să rămână ofertă, ca acel ecran să arate momentul introducerii liniilor.
        cls.so_invoiced = cls._make_order(cls.boiler, 2)
        cls.so_invoiced.action_confirm()
        cls.invoice = cls.so_invoiced._create_invoices()

    @classmethod
    def _make_order(cls, product, qty):
        order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [Command.create({"product_id": product.id, "product_uom_qty": qty})],
            }
        )
        order.order_line.check_extra_product()
        return order

    @classmethod
    def _extra_line_of(cls, order, product):
        return order.order_line.filtered(lambda li: li.product_id == product)

    def test_capture_fise(self):
        # celula de preț unitar a liniei extra (al doilea rând din lista de linii)
        extra_price_cell = "tr.o_data_row:nth-child(2) td[name='price_unit']"
        self.capture_screenshots(
            [
                # 1. Configurarea Extra Line pe fișa produsului principal
                {
                    "url": f"id={self.boiler.product_tmpl_id.id}&model=product.template&view_type=form",
                    "name": "01_configurare_produs.png",
                    "wait": ".o_form_view",
                    "click_tab": "Vânzări",
                    # un singur selector pentru toate cele trei câmpuri: toate primesc contur, iar
                    # bulina apare doar pe primul, ca badge-urile să nu acopere valorile
                    "highlight": ["div[name^='extra_']"],
                    "settle": 2500,
                    "full": True,
                },
                # 2. Comanda cu linia extra generată automat
                {
                    "url": f"id={self.so_auto.id}&model=sale.order&view_type=form",
                    "name": "02_comanda_linie_extra.png",
                    "wait": ".o_form_view",
                    "highlight": ["tr.o_data_row:nth-child(2)"],
                    "settle": 2500,
                    "full": True,
                },
                # 3. Cantitatea liniei extra urmează linia principală (× Extra Qty)
                {
                    "url": f"id={self.so_qty.id}&model=sale.order&view_type=form",
                    "name": "03_cantitate_sincronizata.png",
                    "wait": ".o_form_view",
                    "highlight": ["tr.o_data_row:nth-child(2) td[name='product_uom_qty']"],
                    "settle": 2500,
                    "full": True,
                },
                # 4. Preț negociat manual pe linia extra, păstrat
                {
                    "url": f"id={self.so_manual.id}&model=sale.order&view_type=form",
                    "name": "04_pret_manual.png",
                    "wait": ".o_form_view",
                    "highlight": [extra_price_cell],
                    "settle": 2500,
                    "full": True,
                },
                # 5. Linia extra regenerată, cu prețul calculat din procent
                {
                    "url": f"id={self.so_reset.id}&model=sale.order&view_type=form",
                    "name": "05_revenire_pret_calculat.png",
                    "wait": ".o_form_view",
                    "highlight": [extra_price_cell],
                    "settle": 2500,
                    "full": True,
                },
                # 6. Factura ciornă cu linia extra preluată din comandă
                {
                    "url": f"id={self.invoice.id}&model=account.move&view_type=form",
                    "name": "06_factura_linie_extra.png",
                    "wait": ".o_form_view",
                    "highlight": ["tr.o_data_row:nth-child(2)"],
                    "settle": 3000,
                    "full": True,
                },
            ],
            viewport=(1600, 1100),
        )
