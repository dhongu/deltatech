# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa consultant „Încasări cu cardul și decontarea lor" — generate în
# timpul testelor, în limba RO, pe planul de conturi românesc (`setup_country("ro")`).
#
# Seed: un terminal pe jurnalul „ING card" (5125), o ofertă plătită integral cu cardul (factura de
# avans standard, 3.184,27 lei), o factură plătită parțial (301,59 lei), o încasare pe client
# (33,17 lei), o încasare care nu intră în combinație (120,00 lei) și una întârziată (450,00 lei).
# Linia de extras de 3.519,03 = 3.184,27 + 301,59 + 33,17 se decontează între capturi.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i l10n_ro,deltatech_expected_receipt,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import json
import unittest
from datetime import timedelta

from odoo import Command, fields
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


def _do_action(action, then_click=None, clear=False):
    """JS: deschide o acțiune (dialog) peste ecranul curent și, opțional, apasă un buton din ea."""
    click = (
        f"await new Promise((r) => setTimeout(r, 1500));document.querySelector({json.dumps(then_click)})?.click();"
        if then_click
        else ""
    )
    options = json.dumps({"clearBreadcrumbs": clear})
    return (
        "(async () => {"
        f"await odoo.__WOWL_DEBUG__.root.env.services.action.doAction({json.dumps(action)}, {options});"
        f"{click}"
        "})()"
    )


@tagged("-at_install", "post_install", "fise_screenshots")
class TestExpectedReceiptScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_expected_receipt"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil; capturile fișei se sar")
        super().setUpClass()
        env = cls.env
        manager = env.ref("deltatech_expected_receipt.group_manager")
        sales = env.ref("sales_team.group_sale_manager")
        env.user.group_ids = [Command.link(manager.id), Command.link(sales.id)]
        cls.prepare_ro_company(name="Demo Mobilier SRL")
        company = env.company
        admin = env.ref("base.user_admin")
        admin.write(
            {
                "company_ids": [Command.link(company.id)],
                "company_id": company.id,
                "name": "Maria Ionescu",
                "group_ids": [Command.link(manager.id), Command.link(sales.id)],
            }
        )

        def account(code):
            return env["account.account"].search(
                [("code", "=like", code + "%"), ("company_ids", "in", company.ids)], order="code", limit=1
            )

        company.downpayment_account_id = account("419")
        # Încasările se fac ca utilizatorul care face capturile (casierul terminalului), în RO:
        # „Încasat de” și etichetele notelor (avans, plată) apar ca în realitate.
        cls.admin_env = env(user=admin, context=dict(env.context, lang="ro_RO"))
        cls.journal = cls.admin_env["account.journal"].create(
            {"name": "ING card", "code": "INGC", "type": "bank", "company_id": company.id}
        )
        cls.journal.suspense_account_id.reconcile = True
        cls.terminal = env["deltatech.card.terminal"].create(
            {"name": "Terminal ING Showroom", "user_id": admin.id, "journal_id": cls.journal.id}
        )

        ro = env.ref("base.ro").id
        cls.alfa, cls.beta, cls.gamma, cls.delta, cls.epsilon = env["res.partner"].create(
            [
                {"name": "Alfa Construct SRL", "is_company": True, "country_id": ro, "lang": "ro_RO"},
                {"name": "Beta Design SRL", "is_company": True, "country_id": ro, "lang": "ro_RO"},
                {"name": "Gamma Retail SRL", "is_company": True, "country_id": ro, "lang": "ro_RO"},
                {"name": "Delta Office SRL", "is_company": True, "country_id": ro, "lang": "ro_RO"},
                {"name": "Epsilon Interior SRL", "is_company": True, "country_id": ro, "lang": "ro_RO"},
            ]
        )
        tax_21 = env["account.tax"].search(
            [("type_tax_use", "=", "sale"), ("amount", "=", 21.0), ("company_id", "=", company.id)], limit=1
        )
        product = env["product.product"].create(
            {
                "name": "Canapea extensibilă Nova",
                "type": "consu",
                "list_price": 2631.63,
                "invoice_policy": "order",
                "taxes_id": [Command.set(tax_21.ids)],
            }
        )
        # Oferta: 2.631,63 + TVA 21% 552,64 = 3.184,27 lei, plătită integral cu cardul.
        # Lista de prețuri de test din `product` are nume englezesc; în manual apare cea standard.
        env["product.pricelist"].search([("name", "=", "Test Pricelist")]).name = "Listă de prețuri standard"
        cls.order = env["sale.order"].create(
            {
                "name": "S00001",
                "partner_id": cls.alfa.id,
                "order_line": [Command.create({"product_id": product.id, "product_uom_qty": 1})],
            }
        )
        # Factura de 5.000 + TVA 1.050 = 6.050 lei, din care clientul plătește 301,59 cu cardul.
        cls.invoice = env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.beta.id,
                "invoice_date": fields.Date.context_today(env.user) - timedelta(days=5),
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Mobilier birou — set complet",
                            "price_unit": 5000.0,
                            "tax_ids": [Command.set(tax_21.ids)],
                        }
                    )
                ],
            }
        )
        cls.invoice.action_post()
        cls.today = fields.Date.context_today(env.user)
        cls.act_receipts = env.ref("deltatech_expected_receipt.action_expected_receipt").id
        env.flush_all()

    # ------------------------------------------------------------------
    @classmethod
    def _pay(cls, amount, days_ago, record=None, partner=None):
        context = {"active_model": record._name, "active_id": record.id} if record else {}
        with Form(cls.admin_env["deltatech.card.payment"].with_context(**context)) as form:
            if not record:
                form.partner_id = partner
            form.amount = amount
            form.date = cls.today - timedelta(days=days_ago)
            form.terminal_id = cls.terminal
        form.record.action_confirm()
        return cls.admin_env["deltatech.expected.receipt"].search([], order="id desc", limit=1)

    def _register_payments(self):
        self.r_order = self._pay(3184.27, 3, record=self.order)
        self.r_invoice = self._pay(301.59, 2, record=self.invoice)
        self.r_partner = self._pay(33.17, 1, partner=self.gamma)
        self._pay(120.00, 1, partner=self.delta)
        self._pay(450.00, 6, partner=self.epsilon)
        self.statement_line = self.env["account.bank.statement.line"].create(
            {
                "journal_id": self.journal.id,
                "date": self.today,
                "payment_ref": "ING decontare POS — Terminal ING Showroom",
                "amount": 3519.03,
            }
        )
        self.env.flush_all()

    def _settle(self):
        wizard = self.admin_env["deltatech.card.settlement"].create(
            {"statement_line_id": self.statement_line.id, "company_id": self.env.company.id}
        )
        wizard.action_search()
        self.assertEqual(wizard.state, "proposed")
        wizard.action_settle()
        self.assertEqual(set((self.r_order | self.r_invoice | self.r_partner).mapped("state")), {"settled"})
        self.env.flush_all()

    def _settlement_action(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Decontare card",
            "res_model": "deltatech.card.settlement",
            "views": [[False, "form"]],
            "target": "new",
            "context": {
                "default_statement_line_id": self.statement_line.id,
                "default_company_id": self.env.company.id,
            },
        }

    # ------------------------------------------------------------------
    def test_capture_fise(self):
        # Faza 1 — înainte de încasare: configurare și dialogurile de încasare.
        self.capture_screenshots(
            [
                {
                    "url": f"id={self.terminal.id}&model=deltatech.card.terminal&view_type=form",
                    "name": "01_terminal.png",
                    "wait": ".o_form_view",
                },
                {
                    "url": f"id={self.order.id}&model=sale.order&view_type=form",
                    "name": "02_oferta_buton_card.png",
                    "wait": ".o_form_view",
                    "highlight": ["button[name='action_card_payment']"],
                },
                {
                    "url": f"id={self.order.id}&model=sale.order&view_type=form",
                    "name": "03_incasare_comanda.png",
                    "wait": ".o_form_view",
                    "click_btn": "button[name='action_card_payment']",
                    "wait_after": ".modal-content .o_form_view",
                    "settle": 2000,
                },
                {
                    "url": f"id={self.invoice.id}&model=account.move&view_type=form",
                    "name": "04_incasare_factura.png",
                    "wait": ".o_form_view",
                    "click_btn": "button[name='action_card_payment']",
                    "wait_after": ".modal-content .o_form_view",
                    "settle": 2000,
                },
                {
                    "url": f"action={self.act_receipts}",
                    "name": "05_incasare_client.png",
                    "wait": ".o_list_view, .o_view_nocontent",
                    # fereastra din meniu, completată ca în exemplul fișei (Gamma Retail, 33,17 lei)
                    "eval": _do_action(
                        {
                            "type": "ir.actions.act_window",
                            "name": "Încasare cu cardul",
                            "res_model": "deltatech.card.payment",
                            "views": [[False, "form"]],
                            "target": "new",
                            "context": {"default_partner_id": self.gamma.id, "default_amount": 33.17},
                        }
                    ),
                    "eval_wait": 2500,
                },
            ]
        )

        self._register_payments()
        downpayment = self.r_order.invoice_id

        # Faza 2 — încasările înregistrate și căutarea combinației.
        self.capture_screenshots(
            [
                self.account_move_shot(downpayment, "06_factura_avans.png"),
                self.account_move_shot(self.r_order.payment_id.move_id, "07_nota_incasare.png"),
                {
                    "url": f"id={self.invoice.id}&model=account.move&view_type=form",
                    "name": "08_factura_platita_partial.png",
                    "wait": ".o_form_view",
                    "full": True,
                },
                {
                    "url": f"action={self.act_receipts}",
                    "name": "09_registru_in_asteptare.png",
                    "wait": ".o_list_view",
                },
                {
                    "url": f"action={self.act_receipts}",
                    "name": "10_decontare_linie_extras.png",
                    "wait": ".o_list_view",
                    "eval": _do_action(self._settlement_action()),
                    "eval_wait": 2500,
                },
                {
                    "url": f"action={self.act_receipts}",
                    "name": "11_decontare_combinatie.png",
                    "wait": ".o_list_view",
                    "eval": _do_action(self._settlement_action(), ".modal-footer button[name='action_search']"),
                    "eval_wait": 3500,
                },
            ]
        )

        self._settle()

        # Faza 3 — după decontare.
        self.capture_screenshots(
            [
                {
                    "url": f"action={self.act_receipts}",
                    "name": "12_registru_dupa_decontare.png",
                    "wait": ".o_list_view",
                    "eval": _do_action(
                        {
                            "type": "ir.actions.act_window",
                            "name": "Încasări așteptate",
                            "res_model": "deltatech.expected.receipt",
                            "views": [[False, "list"]],
                            "context": {},
                        },
                        clear=True,
                    ),
                    "eval_wait": 2500,
                },
                self.account_move_shot(self.statement_line.move_id, "13_nota_decontare.png"),
            ]
        )
