# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Încasarea comenzilor de vânzare" — generate în timpul
# testelor, în limba RO, pe compania „Demo Încasări SRL" în RON.
#
# Seedează un procesator „Transfer bancar" și patru
# comenzi de 1.210,00 lei (2 × 500 lei + TVA 21%): fără plată, două cu plata în
# așteptare, una încasată parțial (500 lei). Prima comandă în așteptare se confirmă prin
# fereastra „Confirmă încasarea", ca pasul 4 să arate exact comanda din pașii 1–3.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_sale_payment,payment_custom,l10n_ro,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# meniul ⚙ Acțiuni al formularului și elementul adăugat de modul
ACTION_MENU = ".o_cp_action_menus button"
DROPDOWN = ".o-dropdown--menu"
CONFIRM_ITEM = ".o-dropdown--menu .o-dropdown-item:has-text('Confirmă încasarea')"
OPEN_CONFIRM_WIZARD = (
    "[...document.querySelectorAll('.o-dropdown--menu .o-dropdown-item')]"
    ".find(e => e.textContent.includes('Confirmă încasarea')).click()"
)
# bulina numerotată a evidențierii stă peste colțul stâng al câmpului și acoperea prima
# cifră a sumei („.210,00 lei"); spațiul din stânga o mută lângă valoare
PAD_HIGHLIGHTED = (
    "document.head.insertAdjacentHTML('beforeend', '<style>"
    "div[name=payment_amount], div[name=payment_status], .modal div[name=amount]"
    " {padding-left: 22px !important}</style>')"
)


@tagged("-at_install", "post_install", "fise_screenshots")
class TestSalePaymentScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_sale_payment"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        company = cls.prepare_ro_company(name="Demo Încasări SRL")
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        sale_manager = env.ref("sales_team.group_sale_manager")
        env.user.group_ids = [Command.link(sale_manager.id)]
        admin.group_ids = [Command.link(sale_manager.id)]
        env.flush_all()

        method = env.ref("payment_custom.payment_method_wire_transfer", raise_if_not_found=False)
        if not method:
            method = env["payment.method"].search([("code", "=", "wire_transfer")], limit=1)
        bank_journal = env["account.journal"].search([("type", "=", "bank"), ("company_id", "=", company.id)], limit=1)
        # în 20, utilizatorul testului nu citește payment.method: procesatorul și
        # tranzacțiile se seedează ca superutilizator
        cls.provider = (
            env["payment.provider"]
            .sudo()
            .create(
                {
                    "name": "Transfer bancar",
                    "code": "custom",
                    "custom_mode": "wire_transfer",
                    "company_id": company.id,
                    "journal_id": bank_journal.id,
                    "payment_method_ids": [Command.set(method.ids)],
                }
            )
        )
        cls.method = method

        cls.partner = env["res.partner"].create(
            {"name": "Magazin Exemplu SRL", "country_id": env.ref("base.ro").id, "is_company": True}
        )
        # numele implicit al listei de prețuri a testului e în engleză („Test Pricelist")
        cls.partner.property_product_pricelist.name = "Listă de prețuri RON"
        cls.admin = admin
        tax = company.account_sale_tax_id
        cls.product = env["product.product"].create(
            {
                "name": "Aparat de cafea espresso",
                "type": "consu",
                "list_price": 500.0,
                "taxes_id": [Command.set(tax.ids)],
            }
        )

        cls.order_without = cls._create_order()
        cls.order_pending = cls._create_order()
        cls._create_tx(cls.order_pending, 1210.0, "pending")
        cls.order_partial = cls._create_order(confirm=True)
        cls._create_tx(cls.order_partial, 500.0, "done")
        # a doua comandă în așteptare: după confirmarea primeia, lista are tot un grup
        # „În așteptare"
        cls.order_pending_other = cls._create_order()
        cls._create_tx(cls.order_pending_other, 1210.0, "pending")
        env.flush_all()

        orders = cls.order_without | cls.order_pending | cls.order_partial | cls.order_pending_other
        cls.list_action = env["ir.actions.act_window"].create(
            {
                "name": "Comenzi",
                "res_model": "sale.order",
                "view_mode": "list,form",
                "domain": [("id", "in", orders.ids)],
                "context": {"search_default_group_payment_status": 1},
            }
        )

    @classmethod
    def _create_order(cls, confirm=False):
        order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                # agentul implicit ar fi utilizatorul de test, cu un nume fantezist în engleză
                "user_id": cls.admin.id,
                "order_line": [Command.create({"product_id": cls.product.id, "product_uom_qty": 2})],
            }
        )
        if confirm:
            order.action_confirm()
        return order

    @classmethod
    def _create_tx(cls, order, amount, state):
        return (
            cls.env["payment.transaction"]
            .sudo()
            .create(
                {
                    "provider_id": cls.provider.id,
                    "payment_method_id": cls.method.id,
                    "reference": f"{order.name}-{amount:.0f}",
                    "amount": amount,
                    "currency_id": order.currency_id.id,
                    "partner_id": order.partner_id.id,
                    "state": state,
                    "sale_order_ids": [Command.link(order.id)],
                }
            )
        )

    def _confirm_payment_as_operator(self):
        """Ce face operatorul la pasul 3: Confirmă în fereastră."""
        order = self.order_pending
        wizard_model = self.env["sale.confirm.payment"].with_context(active_id=order.id, active_model="sale.order")
        wizard = wizard_model.create(wizard_model.default_get(list(wizard_model._fields)))
        self.assertEqual(wizard.amount, 1210.0)
        wizard.do_confirm()
        self.assertEqual(order.transaction_ids.state, "done")
        self.env.flush_all()
        self.assertEqual(order.payment_status, "done")

    def test_capture_fise(self):
        self.assertEqual(self.order_pending.amount_total, 1210.0)
        self.assertEqual(self.order_pending.payment_status, "pending")
        self.assertEqual(self.order_partial.payment_status, "partial")
        pending_url = f"id={self.order_pending.id}&model=sale.order&view_type=form"
        payment_fields = ["div[name='payment_amount']", "div[name='payment_status']"]
        self.capture_screenshots(
            [
                # 1. Comanda cu plata prin transfer bancar în așteptare
                {
                    "url": pending_url,
                    "name": "01_comanda_plata_in_asteptare.png",
                    "wait": ".o_form_view",
                    "eval": PAD_HIGHLIGHTED,
                    "settle": 2500,
                    "highlight": payment_fields,
                },
                # 2. ⚙ Acțiuni → Confirmă încasarea
                {
                    "url": pending_url,
                    "name": "02_meniu_actiuni_confirma_incasarea.png",
                    "wait": ".o_form_view",
                    "click_btn": ACTION_MENU,
                    "wait_after": DROPDOWN,
                    "settle": 1500,
                    "highlight": [CONFIRM_ITEM],
                },
                # 3. Fereastra precompletată din tranzacția în așteptare
                {
                    "url": pending_url,
                    "name": "03_wizard_confirma_incasarea.png",
                    "wait": ".o_form_view",
                    "click_btn": ACTION_MENU,
                    "wait_after": DROPDOWN,
                    "eval": OPEN_CONFIRM_WIZARD + "; " + PAD_HIGHLIGHTED,
                    "eval_wait": 3000,
                    "settle": 1500,
                    "highlight": [".modal div[name='amount']", ".modal button[name='do_confirm']"],
                },
            ]
        )
        self._confirm_payment_as_operator()
        self.capture_screenshots(
            [
                # 4. Aceeași comandă, după Confirmă
                {
                    "url": pending_url,
                    "name": "04_comanda_incasata.png",
                    "wait": ".o_form_view",
                    "eval": PAD_HIGHLIGHTED,
                    "settle": 2500,
                    "highlight": payment_fields,
                },
                # 5. Lista comenzilor grupată după starea încasării
                {
                    "url": f"action={self.list_action.id}",
                    "name": "05_lista_grupata_stare_incasare.png",
                    "wait": ".o_list_view",
                    "eval": "document.querySelectorAll('.o_group_header').forEach(h => h.click())",
                    "eval_wait": 2000,
                    "settle": 1500,
                },
            ]
        )
