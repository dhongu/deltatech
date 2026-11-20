# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Proces-verbal de dezmembrare" — generate în timpul testelor, în
# limba RO (fișă) și EN (readme/USAGE.md), pe compania „Demo Dezmembrări SRL" în RON.
#
# Seed: „Set de scule 12 piese" (mărfuri, cont 371, FIFO, evaluare automată), intrat în stoc în trei
# loturi FIFO (5 × 100, 5 × 120, 10 × 130). Procesul-verbal validat dezmembrează 7 bucăți
# (5 × 100 + 2 × 120 = 740 lei cost real) în două articole rezultate, un deșeu recuperabil cu valoare
# fixă și două pierderi (în normă și peste normă). Un al doilea proces-verbal rămâne în ciornă, iar
# un al treilea cere mai mult stoc decât există (dialogul de eroare).
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i l10n_ro,deltatech_stock_disassembly,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots/deltatech_stock_disassembly --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestDisassemblyScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_stock_disassembly"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Dezmembrări SRL")
        company = cls.env.company
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        for xmlid in ("stock.group_stock_manager", "stock.group_stock_multi_locations"):
            group = env.ref(xmlid)
            admin.group_ids = [Command.link(group.id)]
            env.user.group_ids = [Command.link(group.id)]
        env.flush_all()

        def account(prefix):
            return env["account.account"].search(
                [("code", "=like", f"{prefix}%"), ("company_ids", "in", [company.id])], order="code", limit=1
            )

        if not company.account_stock_journal_id:
            company.account_stock_journal_id = env["account.journal"].create(
                {"name": "Operațiuni de stoc", "code": "STJ", "type": "general", "company_id": company.id}
            )
        category = env["product.category"].create(
            {
                "name": "Mărfuri",
                "property_cost_method": "fifo",
                "property_valuation": "real_time",
                "property_stock_valuation_account_id": account("371").id,
                "property_account_expense_categ_id": account("607").id,
            }
        )

        def product(name, cost):
            return env["product.product"].create(
                {
                    "name": name,
                    "type": "consu",
                    "is_storable": True,
                    "categ_id": category.id,
                    "standard_price": cost,
                    "company_id": company.id,
                }
            )

        cls.kit = product("Set de scule 12 piese", 110.0)
        cls.screwdriver = product("Șurubelniță cu cap schimbabil", 40.0)
        cls.wrench = product("Cheie fixă 17", 25.0)
        cls.scrap_metal = product("Deșeu metalic recuperabil", 0.0)
        cls.loss_tech = product("Pierdere tehnologică (praf metalic)", 0.0)
        cls.loss_over = product("Piese distruse peste normă", 0.0)

        warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        cls.stock_location = warehouse.lot_stock_id
        supplier = env.ref("stock.stock_location_suppliers")
        for qty, cost in ((5, 100.0), (5, 120.0), (10, 130.0)):
            move = env["stock.move"].create(
                {
                    "product_id": cls.kit.id,
                    "product_uom": cls.kit.uom_id.id,
                    "product_uom_qty": qty,
                    "location_id": supplier.id,
                    "location_dest_id": cls.stock_location.id,
                    "picking_type_id": warehouse.in_type_id.id,
                    "price_unit": cost,
                    "value_manual": cost * qty,
                }
            )
            move._action_confirm()
            move._action_assign()
            move.picked = True
            move._action_done()

        # numerotare deterministă: PVD/<an>/00001 la fiecare rulare
        env["ir.sequence"].search([("code", "=", "stock.disassembly")]).number_next_actual = 1
        cls.done_report = cls._make_report(7, "Set neutilizabil ca atare, recuperat pe componente")
        cls.done_report.action_validate()
        cls.draft_report = cls._make_report(2, "Set cu piese lipsă, de recuperat pe componente")
        cls.error_report = env["stock.disassembly"].create(
            {
                "product_id": cls.kit.id,
                "product_qty": 50,
                "location_id": cls.stock_location.id,
                "reason": "Cantitate mai mare decât stocul",
                "line_ids": [
                    Command.create({"product_id": cls.screwdriver.id, "quantity": 50, "reference_price": 40.0})
                ],
            }
        )
        env.flush_all()

    @classmethod
    def _make_report(cls, qty, reason):
        return cls.env["stock.disassembly"].create(
            {
                "product_id": cls.kit.id,
                "product_qty": qty,
                "location_id": cls.stock_location.id,
                "allocation_method": "price",
                "reason": reason,
                "committee": "Ionescu Maria, șef depozit\nPopescu Andrei, gestionar\nGeorgescu Ana, contabil",
                "line_ids": [
                    Command.create({"product_id": cls.screwdriver.id, "quantity": qty * 12, "reference_price": 40.0}),
                    Command.create({"product_id": cls.wrench.id, "quantity": qty * 12, "reference_price": 25.0}),
                    Command.create(
                        {
                            "product_id": cls.scrap_metal.id,
                            "quantity": qty,
                            "use_fixed_value": True,
                            "fixed_value": 10.0 * qty,
                            "reference_price": 0.0,
                        }
                    ),
                    Command.create({"line_type": "scrap", "product_id": cls.loss_tech.id, "quantity": 1}),
                    Command.create(
                        {
                            "line_type": "scrap",
                            "product_id": cls.loss_over.id,
                            "quantity": 2,
                            "over_norm": True,
                            "use_fixed_value": True,
                            "fixed_value": 30.0,
                        }
                    ),
                ],
            }
        )

    def _shots(self, lang="ro_RO"):
        env = self.env
        action = env.ref("deltatech_stock_disassembly.action_stock_disassembly")
        menu = env.ref("deltatech_stock_disassembly.menu_stock_disassembly")
        settings = env.ref("stock.action_stock_config_settings")
        model = "stock.disassembly"
        return [
            {
                "url": f"action={action.id}&menu_id={menu.id}&model={model}&view_type=list",
                "name": "01_lista_procese_verbale.png",
                "wait": ".o_list_view",
                "highlight": [".o_list_button_add"],
            },
            {
                "url": f"id={self.draft_report.id}&action={action.id}&menu_id={menu.id}&model={model}&view_type=form",
                "name": "02_ciorna_rezultate.png",
                "wait": ".o_form_view",
                "settle": 2500,
                "highlight": [
                    "div[name='product_id']",
                    "div[name='allocation_method']",
                    "button[name='action_validate']",
                ],
            },
            {
                "url": f"id={self.draft_report.id}&action={action.id}&menu_id={menu.id}&model={model}&view_type=form",
                "name": "03_comisie_motiv.png",
                "wait": ".o_form_view",
                "click_tab": {"ro_RO": "Comisie și motiv", "en_US": "Committee and Reason"},
                "settle": 2000,
                "highlight": ["[name='reason']", "[name='committee']"],
            },
            {
                "url": f"id={self.done_report.id}&action={action.id}&menu_id={menu.id}&model={model}&view_type=form",
                "name": "04_validat.png",
                "wait": ".o_form_view",
                "settle": 2500,
                "highlight": ["div[name='value']", "button[name='action_view_account_move']"],
            },
            {
                "url": f"id={self.done_report.id}&action={action.id}&menu_id={menu.id}&model={model}&view_type=form",
                "name": "05_miscari_stoc.png",
                "wait": ".o_form_view",
                "click_btn": "button[name='action_view_moves']",
                "wait_after": ".o_pivot",
                "eval": "document.querySelector('.o_switch_view.o_list').click();",
                "settle": 3500,
            },
            self.account_move_shot(self.done_report.account_move_id, "06_nota_contabila.png"),
            self.report_shot(
                "deltatech_stock_disassembly.report_stock_disassembly",
                self.done_report,
                "07_proces_verbal_pdf.png",
                lang=lang,
            ),
            {
                "url": f"id={self.error_report.id}&action={action.id}&menu_id={menu.id}&model={model}&view_type=form",
                "name": "08_stoc_insuficient.png",
                "wait": ".o_form_view",
                "click_btn": "button[name='action_validate']",
                "wait_after": ".o_form_view",
                "settle": 4500,
            },
            {
                "url": f"action={settings.id}&model=res.config.settings&view_type=form",
                "name": "09_setari_reclasificare.png",
                "wait": ".o_form_view",
                "timeout": 40000,
                "eval": (
                    "const el = document.querySelector(\"[name='disassembly_allow_reclassification']\");"
                    " if (el) { el.scrollIntoView({block: 'center'}); }"
                ),
                "settle": 3000,
                "highlight": ["div[name='disassembly_allow_reclassification']"],
            },
        ]

    def test_capture_fise(self):
        # raportul se randează în limba partenerului companiei (t-lang din șablon)
        self.env.company.partner_id.lang = "ro_RO"
        self.capture_screenshots(self._shots())

    def test_capture_usage(self):
        self.env.company.partner_id.lang = "en_US"
        self.capture_screenshots(self._shots("en_US"), lang="en_US")
