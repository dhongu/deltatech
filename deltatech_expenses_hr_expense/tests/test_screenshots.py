# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa consultant a punții `deltatech_expenses_hr_expense` — generate în
# timpul testelor, în limba RO, pe planul de conturi românesc (`setup_country("ro")`).
#
# Doar pasul propriu punții: preluarea unei cheltuieli din `hr.expense` în decont (wizard) și
# cheltuiala legată. Restul fluxului (avans, decontare, note) are capturile în deltatech_expenses.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_expenses_hr_expense,l10n_ro_doc_screenshots \
#       --test-tags=/deltatech_expenses_hr_expense:TestExpensesScreenshots --stop-after-init
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
    screenshots_module = "deltatech_expenses_hr_expense"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        # tooling-ul de capturi (l10n_ro_doc_screenshots) poate lipsi de pe disc (alt repo) —
        # în acest caz sărim întreaga clasă, nu o lăsăm să cadă pe `object`
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil; capturile fișei se sar")
        super().setUpClass()
        # AccountTestInvoicingCommon rulează cu un user de test dedicat ("accountman"), nu cu
        # superuser/admin — are nevoie explicit de rolul de Contabil ca să poată crea/valida
        # deconturi (grupurile noi angajat/aprobator/contabil, tichet POPVAL-COS).
        cls.env.user.group_ids = [(4, cls.env.ref("deltatech_expenses.group_expenses_accounting").id)]
        cls.prepare_ro_company(name="Demo Deconturi SRL")  # RON, drepturi contabile + limba RO
        company = cls.env.company
        cls.env.ref("base.user_admin").write({"company_ids": [(4, company.id)], "company_id": company.id})
        env = cls.env

        def account(code):
            return env["account.account"].search(
                [("code", "=like", code + "%"), ("company_ids", "in", [company.id])], order="code", limit=1
            )

        cls.acc_542 = account("542") or env["account.account"].create(
            {"name": "Avansuri de trezorerie", "code": "542000", "account_type": "asset_current"}
        )
        cls.acc_625 = (
            account("625")
            or account("623")
            or env["account.account"].create(
                {"name": "Cheltuieli cu deplasări", "code": "625000", "account_type": "expense"}
            )
        )

        cls.cash_journal = env["account.journal"].search(
            [("type", "=", "cash"), ("company_id", "=", company.id)], limit=1
        ) or env["account.journal"].create({"name": "Casa", "code": "CASA", "type": "cash", "company_id": company.id})
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
            [("type", "=", "general"), ("company_id", "=", company.id)], limit=1
        )

        cls.tax = env["account.tax"].search(
            [("type_tax_use", "=", "purchase"), ("company_id", "=", company.id), ("amount", "=", 21.0)],
            limit=1,
        ) or env["account.tax"].search(
            [("type_tax_use", "=", "purchase"), ("company_id", "=", company.id), ("amount", ">", 0)], limit=1
        )

        # angajat cu partener (work_contact_id) — seeding ca contabil => sudo pentru hr.employee
        cls.partner = env["res.partner"].create({"name": "Ionescu Andrei", "country_id": env.ref("base.ro").id})
        cls.employee = env["hr.employee"].sudo().create({"name": "Ionescu Andrei", "work_contact_id": cls.partner.id})
        cls.supplier = env["res.partner"].create({"name": "Hotel Carpați SRL", "is_company": True})

        # ---- Scenariul A: decont în starea „Avans", în care se preiau cheltuielile ------------
        cls.decont = cls._make_deduction(advance=1000.0, diem=42.5, days=2)
        cls.decont.validate_advance()  # state -> advance, creează nota de avans (542 = 5311)
        for label, amount in (("Cazare hotel", 500.0), ("Transport", 300.0)):
            cls._make_line(cls.decont, label, amount)

        # ---- Scenariul B: preluarea unei cheltuieli din hr.expense (capturi 03 + 04) ----------
        product = (
            env["product.product"].sudo().create({"name": "Bilet avion", "can_be_expensed": True, "type": "consu"})
        )
        cls.hr_expense = (
            env["hr.expense"]
            .sudo()
            .create(
                {
                    "name": "Bilet avion București-Cluj",
                    "employee_id": cls.employee.id,
                    "product_id": product.id,
                    "total_amount_currency": 484.0,
                    "tax_ids": [(6, 0, cls.tax.ids)] if cls.tax else False,
                    "account_id": cls.acc_625.id,
                }
            )
        )
        cls.hr_expense.sudo().approval_state = "approved"  # devine eligibilă
        # wizardul de preluare (persistă în tranzacție => capturabil)
        cls.wizard = (
            env["deltatech.expenses.import.hr"].with_context(default_expenses_deduction_id=cls.decont.id).create({})
        )
        # preluăm cheltuiala în decont (adaugă o linie + leagă cheltuiala)
        cls.decont._import_hr_expenses(cls.hr_expense)

    @classmethod
    def _make_deduction(cls, advance, diem, days):
        return cls.env["deltatech.expenses.deduction"].create(
            {
                "date_advance": fields.Date.today(),
                "employee_id": cls.employee.id,
                "advance": advance,
                "diem": diem,
                "days": days,
                "journal_id": cls.cash_journal.id,
                "expense_journal_id": cls.adv_journal.id,
                "journal_diem_id": cls.diem_journal.id,
                "account_diem_id": cls.acc_625.id,
            }
        )

    @classmethod
    def _make_line(cls, deduction, label, amount):
        return cls.env["deltatech.expenses.deduction.line"].create(
            {
                "expenses_deduction_id": deduction.id,
                "name": label,
                "amount": amount,
                "tax_ids": [(6, 0, cls.tax.ids)] if cls.tax else False,
                "expense_account_id": cls.acc_625.id,
                "partner_id": cls.supplier.id,
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
        shots = [
            # wizardul „Preia cheltuieli HR" (cheltuieli eligibile)
            self._form(self.wizard, "03_preia_hr_wizard.png"),
            # cheltuiala hr.expense legată de decont (banner, postare standard dezactivată)
            self._form(self.hr_expense, "04_hr_expense_legat.png"),
        ]
        self.capture_screenshots(shots, viewport=(1500, 1150), hide_systray=True)
