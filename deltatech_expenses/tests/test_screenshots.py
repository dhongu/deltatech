# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa consultant „Decont de cheltuieli din avans (542)" — generate în
# timpul testelor, în limba RO, pe planul de conturi românesc (`setup_country("ro")`), fără
# `hr_expense` (capturile preluării din hr.expense sunt în deltatech_expenses_hr_expense).
#
# Acoperă fluxul complet, cu notele contabile la fiecare pas:
#   1. decont în starea „Avans" (avans + linii cu TVA inclus + diurnă) și nota de avans (542 = 5311);
#   2. butonul smart „Deconturi" de pe fișa angajatului;
#   3. decont validat („Efectuat"), chitanța de achiziție (6xx + 4426 = 401), nota de decontare
#      (401 = 542), nota de restituire a diferenței (5311 = 542) și nota de diurnă (625 = 542).
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_expenses,l10n_ro_doc_screenshots \
#       --test-tags=/deltatech_expenses:TestExpensesScreenshots --stop-after-init
import unittest

from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestExpensesScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_expenses"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        # tooling-ul de capturi (l10n_ro_doc_screenshots) poate lipsi de pe disc (alt repo) —
        # în acest caz sărim întreaga clasă, nu o lăsăm să cadă pe `object`
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil; capturile fișei se sar")
        super().setUpClass()
        # AccountTestInvoicingCommon rulează cu un user de test dedicat, nu cu admin — are nevoie
        # explicit de rolul de Contabil ca să poată crea/valida deconturi.
        accounting = cls.env.ref("deltatech_expenses.group_expenses_accounting")
        cls.env.user.group_ids = [(4, accounting.id)]
        cls.prepare_ro_company(name="Demo Deconturi SRL")  # RON, drepturi contabile + limba RO
        company = cls.env.company
        cls.env.ref("base.user_admin").write(
            {"company_ids": [(4, company.id)], "company_id": company.id, "group_ids": [(4, accounting.id)]}
        )
        env = cls.env

        def account(code):
            return env["account.account"].search(
                [("code", "=like", code + "%"), ("company_ids", "in", [company.id])], order="code", limit=1
            )

        def purchase_tax(rate):
            return env["account.tax"].search(
                [
                    ("type_tax_use", "=", "purchase"),
                    ("company_id", "=", company.id),
                    ("amount", "=", rate),
                    ("amount_type", "=", "percent"),
                ],
                limit=1,
            )

        cls.acc_542 = account("542")
        cls.acc_625 = account("625")

        cls.cash_journal = env["account.journal"].search(
            [("type", "=", "cash"), ("company_id", "=", company.id)], limit=1
        ) or env["account.journal"].create({"name": "Casa", "code": "CASA", "type": "cash", "company_id": company.id})
        cls.cash_journal.name = "Casa în lei"
        # jurnalul de avans: contul implicit = 542 (cerința modulului)
        cls.adv_journal = env["account.journal"].create(
            {
                "name": "Avansuri trezorerie",
                "code": "AVTRZ",
                "type": "general",
                "default_account_id": cls.acc_542.id,
                "company_id": company.id,
            }
        )
        cls.diem_journal = env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", company.id), ("id", "!=", cls.adv_journal.id)], limit=1
        )

        # cazarea are cota redusă de 11%, transportul cota standard de 21% (taxe „pe deasupra":
        # suma de pe bon se introduce oricum cu TVA inclus)
        cls.tax_11 = purchase_tax(11.0)
        cls.tax_21 = purchase_tax(21.0)

        # angajat cu partener (work_contact_id) — seeding ca contabil => sudo pentru hr.employee
        cls.partner = env["res.partner"].create({"name": "Ionescu Andrei", "country_id": env.ref("base.ro").id})
        cls.employee = env["hr.employee"].sudo().create({"name": "Ionescu Andrei", "work_contact_id": cls.partner.id})
        cls.hotel = env["res.partner"].create({"name": "Hotel Carpați SRL", "is_company": True})
        cls.train = env["res.partner"].create({"name": "CFR Călători SA", "is_company": True})

        start = fields.Date.subtract(fields.Date.today(), days=4)
        end = fields.Date.subtract(fields.Date.today(), days=2)

        # ---- Scenariul A: decont în starea „Avans" (capturi 01 + 02) -------------------------
        cls.decont = cls._make_deduction("OD-14", start, end)
        cls.decont.validate_advance()  # state -> advance, creează nota de avans (542 = 5311)
        cls._make_lines(cls.decont, start)
        cls.advance_move = env["account.move"].search([("expenses_deduction_id", "=", cls.decont.id)], limit=1)

        # ---- Scenariul B: decont validat complet (capturi 06–10) ------------------------------
        cls.decont_done = cls._make_deduction("OD-12", start, end)
        cls.decont_done.validate_advance()
        cls._make_lines(cls.decont_done, start)
        cls.decont_done.validate_expenses()
        moves = env["account.move"].search([("expenses_deduction_id", "=", cls.decont_done.id)])
        cls.receipt = moves.filtered(lambda m: m.move_type == "in_receipt" and m.partner_id == cls.hotel)
        entries = moves.filtered(lambda m: m.move_type == "entry")
        cls.settle_move = entries.filtered(
            lambda m: any(aml.account_id.account_type == "liability_payable" for aml in m.line_ids)
            and m.line_ids.partner_id & cls.hotel
        )[:1]
        cls.refund_move = entries.filtered(lambda m: m.journal_id == cls.cash_journal and m.date == end)[:1]
        cls.diem_move = cls.decont_done.move_id

    @classmethod
    def _make_deduction(cls, travel_order, start, end):
        return cls.env["deltatech.expenses.deduction"].create(
            {
                "date_advance": start,
                "date_expense": end,
                "travel_order": travel_order,
                "employee_id": cls.employee.id,
                "advance": 1000.0,
                "diem": 42.5,
                "days": 2,
                "journal_id": cls.cash_journal.id,
                "expense_journal_id": cls.adv_journal.id,
                "journal_diem_id": cls.diem_journal.id,
                "account_diem_id": cls.acc_625.id,
            }
        )

    @classmethod
    def _make_lines(cls, deduction, date):
        for label, amount, tax, supplier in (
            ("Cazare hotel, 2 nopți", 555.0, cls.tax_11, cls.hotel),
            ("Bilet tren București–Cluj", 121.0, cls.tax_21, cls.train),
        ):
            cls.env["deltatech.expenses.deduction.line"].create(
                {
                    "expenses_deduction_id": deduction.id,
                    "date": date,
                    "name": label,
                    "amount": amount,
                    "tax_ids": [(6, 0, tax.ids)],
                    "expense_account_id": cls.acc_625.id,
                    "partner_id": supplier.id,
                }
            )

    def _form(self, record, name, **kw):
        shot = {
            "url": f"id={record.id}&model={record._name}&view_type=form",
            "name": name,
            "wait": ".o_form_view",
            "settle": 2000,
            "full": True,
        }
        shot.update(kw)
        return shot

    def test_capture_fise(self):
        action = self.env.ref("deltatech_expenses.action_deltatech_expenses_deduction")

        def deduction_form(record, name, **kw):
            return self._form(
                record, name, url=f"action={action.id}&id={record.id}&model={record._name}&view_type=form", **kw
            )

        shots = [
            # Pasul 1 — decontul în starea „Avans" (avans, linii cu TVA, diurnă, diferență)
            deduction_form(self.decont, "01_decont_avans.png", highlight=["button[name='validate_expenses']"]),
            # Pasul 1 — nota de acordare avans (Dr 542 = Cr 5311)
            self.account_move_shot(self.advance_move, "02_nota_avans.png"),
            # Pasul 3 — fișa angajatului cu butonul smart „Deconturi"
            self._form(
                self.employee,
                "05_angajat_deconturi.png",
                full=False,
                # doar antetul cu butoanele smart; restul fișei angajatului (hr standard) e zgomot
                eval="document.querySelector('.o_form_sheet .o_notebook')?.remove()",
                highlight=["button.oe_stat_button:has-text('Deconturi')"],
            ),
            # Pasul 2 — decontul validat
            deduction_form(self.decont_done, "06_decont_validat.png"),
            # Pasul 2 — nota de decontare din avans (Dr 401 = Cr 542), reconciliată cu chitanța
            self.account_move_shot(self.settle_move, "07_nota_decontare.png"),
            # Pasul 2 — chitanța de achiziție generată (Dr 6xx + Dr 4426 = Cr 401)
            self.account_move_shot(self.receipt, "08_chitanta_achizitie.png"),
            # Pasul 2 — restituirea diferenței în casă (Dr 5311 = Cr 542)
            self.account_move_shot(self.refund_move, "09_nota_restituire.png"),
            # Pasul 2 — nota de diurnă (Dr 625 = Cr 542)
            self.account_move_shot(self.diem_move, "10_nota_diurna.png"),
        ]
        self.capture_screenshots(shots, viewport=(1500, 1150), hide_systray=True)
