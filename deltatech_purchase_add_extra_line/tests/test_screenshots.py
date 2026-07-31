# © 2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Linie suplimentară automată pe comanda de achiziție" — generate
# în timpul testelor, în limba RO, pe compania „RO Company" în RON.
#
# Seedează scenariul comercial din fișă: motor electric + serviciu de transport la 5% din preț
# (Procent suplimentar), în stările de dinainte și de după intervenția manuală pe preț.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_purchase_add_extra_line,l10n_ro,l10n_ro_doc_screenshots \
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
class TestPurchaseAddExtraLineScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_purchase_add_extra_line"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Achiziții SRL")  # RON, drepturi contabile + limba RO
        company = cls.env.company
        cls.env.ref("base.user_admin").write({"company_ids": [(4, company.id)], "company_id": company.id})

        env = cls.env
        # drepturi de achiziții: pe utilizatorul testului (seedul) și pe admin (browserul de capturi)
        purchase_manager = env.ref("purchase.group_purchase_manager", raise_if_not_found=False)
        if purchase_manager:
            env.user.group_ids = [Command.link(purchase_manager.id)]
            env.ref("base.user_admin").group_ids = [Command.link(purchase_manager.id)]
            env.flush_all()

        cls.vendor = env["res.partner"].create(
            {"name": "Electro Furnizor SRL", "country_id": env.ref("base.ro").id, "supplier_rank": 1}
        )

        # Serviciul de transport, facturat ca procent din valoarea mărfii
        cls.transport = env["product.product"].create(
            {"name": "Transport și manipulare", "type": "service", "standard_price": 100.0}
        )
        cls.motor = env["product.product"].create(
            {
                "name": "Motor electric 7,5 kW",
                "type": "consu",
                "standard_price": 2400.0,
                "seller_ids": [Command.create({"partner_id": cls.vendor.id, "price": 2400.0, "min_qty": 1})],
                "extra_product_id": cls.transport.id,
                "extra_percent": 5.0,
                "extra_qty": 1.0,
            }
        )

        # Pasul 2 — cerere de ofertă cu linia suplimentară generată automat (5 motoare)
        cls.rfq_auto = cls._make_order(5)

        # Pasul 3 — cantitatea urmează linia principală (urcată la 8)
        cls.rfq_qty = cls._make_order(5)
        cls._main_line(cls.rfq_qty).product_qty = 8
        cls.rfq_qty.order_line.check_extra_product()

        # Pasul 4 — preț negociat manual, păstrat la modificarea liniei principale
        cls.rfq_manual = cls._make_order(5)
        cls._extra_line(cls.rfq_manual).price_unit = 80.0
        cls._main_line(cls.rfq_manual).product_qty = 8
        cls.rfq_manual.order_line.check_extra_product()

        # Pasul 5 — după ștergerea liniei suplimentare, ea se regenerează cu prețul calculat
        cls.rfq_reset = cls._make_order(5)
        extra_reset = cls._extra_line(cls.rfq_reset)
        extra_reset.price_unit = 80.0
        extra_reset.unlink()
        cls._main_line(cls.rfq_reset).check_extra_product()

        # Pasul 6 — comandă confirmată, cu linia suplimentară preluată
        cls.order_confirmed = cls._make_order(5)
        cls.order_confirmed.button_confirm()

    @classmethod
    def _make_order(cls, qty):
        order = cls.env["purchase.order"].create(
            {
                "partner_id": cls.vendor.id,
                "order_line": [Command.create({"product_id": cls.motor.id, "product_qty": qty})],
            }
        )
        order.order_line.check_extra_product()
        return order

    @classmethod
    def _main_line(cls, order):
        return order.order_line.filtered(lambda li: li.product_id == cls.motor)

    @classmethod
    def _extra_line(cls, order):
        return order.order_line.filtered(lambda li: li.product_id == cls.transport)

    def test_capture_fise(self):
        # celula de preț unitar a liniei suplimentare (al doilea rând din lista de linii)
        extra_price_cell = "tr.o_data_row:nth-child(2) td[name='price_unit']"
        self.capture_screenshots(
            [
                # 1. Configurarea liniei suplimentare pe fișa produsului principal
                {
                    "url": f"id={self.motor.product_tmpl_id.id}&model=product.template&view_type=form",
                    "name": "01_configurare_produs.png",
                    "wait": ".o_form_view",
                    "click_tab": "Achiziții",
                    "highlight": ["div[name^='extra_']"],
                    # fără `full`: pe tot formularul grupul de configurare ar ocupa ~15% din imagine,
                    # cu două benzi goale deasupra; aducem grupul în cadru și pozăm viewportul
                    "eval": "document.querySelector(\"div[name='extra_product_id']\")"
                    ".scrollIntoView({block: 'center'})",
                    "settle": 2500,
                },
                # 2. Cererea de ofertă cu linia suplimentară generată automat
                {
                    "url": f"id={self.rfq_auto.id}&model=purchase.order&view_type=form",
                    "name": "02_comanda_linie_extra.png",
                    "wait": ".o_form_view",
                    "highlight": ["tr.o_data_row:nth-child(2)"],
                    "settle": 2500,
                    "full": True,
                },
                # 3. Cantitatea liniei suplimentare urmează linia principală
                {
                    "url": f"id={self.rfq_qty.id}&model=purchase.order&view_type=form",
                    "name": "03_cantitate_sincronizata.png",
                    "wait": ".o_form_view",
                    "highlight": ["tr.o_data_row:nth-child(2) td[name='product_qty']"],
                    "settle": 2500,
                    "full": True,
                },
                # 4. Preț negociat manual pe linia suplimentară, păstrat
                {
                    "url": f"id={self.rfq_manual.id}&model=purchase.order&view_type=form",
                    "name": "04_pret_manual.png",
                    "wait": ".o_form_view",
                    "highlight": [extra_price_cell],
                    "settle": 2500,
                    "full": True,
                },
                # 5. Linia suplimentară regenerată, cu prețul calculat din procent
                {
                    "url": f"id={self.rfq_reset.id}&model=purchase.order&view_type=form",
                    "name": "05_revenire_pret_calculat.png",
                    "wait": ".o_form_view",
                    "highlight": [extra_price_cell],
                    "settle": 2500,
                    "full": True,
                },
                # 6. Comanda de achiziție confirmată, cu linia suplimentară preluată
                {
                    "url": f"id={self.order_confirmed.id}&model=purchase.order&view_type=form",
                    "name": "06_comanda_confirmata.png",
                    "wait": ".o_form_view",
                    # pe comanda confirmată furnizorul devine link și primește un tooltip care
                    # rămâne deschis în captură; îl dezactivăm prin stil, ca să nu reapară după settle
                    "eval": "const s=document.createElement('style');"
                    "s.textContent='.o-tooltip,.popover,.tooltip{display:none !important}';"
                    "document.head.appendChild(s)",
                    "highlight": ["tr.o_data_row:nth-child(2)"],
                    "settle": 3000,
                    "full": True,
                },
            ],
            viewport=(1600, 1100),
        )
