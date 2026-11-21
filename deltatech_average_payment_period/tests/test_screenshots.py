# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Perioada medie de plată" — generate în timpul testelor, în limba
# RO (fișa) și EN (readme/USAGE.md).
#
# Seed: compania pe planul de conturi RO, doi clienți și un furnizor, facturi achitate la 10, 30 și
# 45 de zile (client) și 20 de zile (furnizor), plus o factură neplătită care nu intră în raport.
#
# Rulare:
#   odoo-bin -c <config> -d <db> -i l10n_ro,deltatech_average_payment_period,deltatech_doc_screenshots \
#       --test-tags=/deltatech_average_payment_period:TestAveragePaymentScreenshots --stop-after-init
import unittest

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# pivotul: antetul „Total" al coloanelor → Dată → Lună
PIVOT_BY_MONTH_JS = """async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const byText = (sel, texts) => [...document.querySelectorAll(sel)]
        .find((el) => texts.includes(el.textContent.trim()));
    document.querySelector('thead .o_pivot_header_cell_closed').click();
    await sleep(600);
    const date = byText('.o-dropdown--menu .dropdown-item, .o-dropdown--menu .o_menu_item', %(date)s);
    date.click();
    await sleep(600);
    const month = byText('.o-dropdown--menu .dropdown-item, .o-dropdown--menu .o_menu_item', %(month)s);
    month.click();
    await sleep(1200);
}"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestAveragePaymentScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_average_payment_period"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Plăți SRL")  # RON, drepturi contabile + limba RO
        env = cls.env
        company = env.company
        env.ref("base.user_admin").write({"company_ids": [(4, company.id)], "company_id": company.id})

        # plata se înregistrează direct pe contul băncii (5121), ca să creeze notă și să se reconcilieze
        cls.bank = cls.company_data["default_journal_bank"]
        methods = cls.bank.inbound_payment_method_line_ids | cls.bank.outbound_payment_method_line_ids
        methods.payment_account_id = cls.bank.default_account_id

        ro = env.ref("base.ro").id
        cls.alfa = env["res.partner"].create({"name": "Client Alfa SRL", "country_id": ro})
        cls.beta = env["res.partner"].create({"name": "Client Beta SRL", "country_id": ro})
        cls.gamma = env["res.partner"].create({"name": "Furnizor Gamma SRL", "country_id": ro})

        cls.tax_sale = cls._tax("sale")
        cls.tax_purchase = cls._tax("purchase")

        base = (fields.Date.today() - relativedelta(months=4)).replace(day=1)
        m0, m1, m2 = base, base + relativedelta(months=1), base + relativedelta(months=2)

        cls._paid("out_invoice", cls.alfa, m0.replace(day=5), 1000.0, 10)
        cls.invoice_alfa = cls._paid("out_invoice", cls.alfa, m1.replace(day=5), 2000.0, 30)
        cls._paid("out_invoice", cls.beta, m0.replace(day=10), 1500.0, 45)
        cls._paid("in_invoice", cls.gamma, m1.replace(day=15), 800.0, 20)
        # factură neplătită: nu apare în raport
        cls._invoice("out_invoice", cls.beta, m2.replace(day=20), 900.0)
        env.flush_all()

    @classmethod
    def _tax(cls, use):
        domain = [("type_tax_use", "=", use), ("company_id", "=", cls.env.company.id)]
        return cls.env["account.tax"].search(domain + [("amount", "=", 21.0)], limit=1) or cls.env[
            "account.tax"
        ].search(domain + [("amount", ">", 0)], limit=1)

    @classmethod
    def _invoice(cls, move_type, partner, date, amount):
        tax = cls.tax_sale if move_type == "out_invoice" else cls.tax_purchase
        move = cls.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": partner.id,
                "invoice_date": date,
                "date": date,
                # termen de 30 de zile: scadența de pe factură e coerentă cu plata din demo
                "invoice_payment_term_id": cls.env.ref("account.account_payment_term_30days").id,
                "invoice_line_ids": [
                    (0, 0, {"name": "Marfă", "quantity": 1, "price_unit": amount, "tax_ids": [(6, 0, tax.ids)]})
                ],
            }
        )
        move.action_post()
        return move

    @classmethod
    def _paid(cls, move_type, partner, date, amount, days):
        move = cls._invoice(move_type, partner, date, amount)
        cls.env["account.payment.register"].with_context(active_model="account.move", active_ids=move.ids).create(
            {"journal_id": cls.bank.id, "payment_date": date + relativedelta(days=days)}
        )._create_payments()
        return move

    def _shots(self):
        report = self.env.ref("deltatech_average_payment_period.action_account_average_payment_report").id
        invoices = self.env.ref("account.action_move_out_invoice_type").id
        return [
            {
                "url": f"action={invoices}&id={self.invoice_alfa.id}&model=account.move&view_type=form",
                "name": "01_factura_platita.png",
                "wait": ".o_form_view",
                "highlight": "div[name='invoice_payments_widget']",
                "settle": 2000,
            },
            {
                "url": f"action={report}&view_type=pivot",
                "name": "02_raport_pe_parteneri.png",
                "wait": ".o_pivot",
                "settle": 2000,
            },
            {
                "url": f"action={report}&view_type=pivot",
                "name": "03_raport_pe_luni.png",
                "wait": ".o_pivot",
                "eval": {
                    "ro_RO": PIVOT_BY_MONTH_JS % {"date": '["Dată"]', "month": '["Luna", "Lună"]'},
                    "en_US": PIVOT_BY_MONTH_JS % {"date": '["Date"]', "month": '["Month"]'},
                },
                "eval_wait": 2500,
                "settle": 2000,
            },
            {
                "url": f"action={report}&view_type=graph",
                "name": "04_grafic_zile_plata.png",
                "wait": ".o_graph_renderer",
                "settle": 2500,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots())

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), lang="en_US")
