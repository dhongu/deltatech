# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.exceptions import UserError


class DeltatechExpensesDeduction(models.Model):
    _inherit = "deltatech.expenses.deduction"

    def _eligible_hr_expenses(self):
        """Cheltuielile hr.expense ale angajatului care pot fi preluate în decont:
        aprobate/depuse, fără notă contabilă proprie și nelegate de alt decont."""
        self.ensure_one()
        if not self.employee_id:
            return self.env["hr.expense"]
        return self.env["hr.expense"].search(
            [
                ("employee_id", "=", self.employee_id.id),
                ("company_id", "=", self.company_id.id),
                ("expenses_deduction_id", "=", False),
                ("state", "in", ("submitted", "approved")),
                ("account_move_id", "=", False),
            ]
        )

    def _import_hr_expenses(self, expenses):
        """Creează linii de decont din cheltuielile hr.expense date și le leagă de decont
        (setând expenses_deduction_id), astfel încât contabilizarea să se facă doar aici.

        Re-validează explicit criteriile de eligibilitate pe TOT ce i se dă (nu doar filtrul din
        wizard, care e doar o preîncărcare): un apel care primește cheltuieli ale altui angajat,
        altei companii, aflate într-o stare neeligibilă sau deja contabilizate este respins, chiar
        dacă interfața ar permite selecția lor (tichet POPVAL-COS)."""
        self.ensure_one()
        if self.state not in ("draft", "advance"):
            # `action_open_import_hr_expenses` verifică asta la deschiderea wizard-ului, dar
            # `action_import`-ul wizard-ului apelează direct această metodă — fără acest guard,
            # un decont deja Finalizat/Anulat ar putea primi în continuare linii noi (runda 2,
            # tichet POPVAL-COS).
            raise UserError(self.env._("Cheltuielile pot fi preluate doar într-un decont în starea Draft sau Advance."))
        line_model = self.env["deltatech.expenses.deduction.line"]
        expenses = expenses.filtered(lambda e: not e.expenses_deduction_id)
        invalid = expenses.filtered(
            lambda e: e.employee_id != self.employee_id
            or e.company_id != self.company_id
            or e.state not in ("submitted", "approved")
            or e.account_move_id
        )
        if invalid:
            raise UserError(
                self.env._(
                    "Următoarele cheltuieli nu pot fi preluate în acest decont (angajat/companie diferite, "
                    "stare neeligibilă sau deja contabilizate): %s"
                )
                % ", ".join(invalid.mapped("name"))
            )
        for expense in expenses:
            # Linia de decont interpretează `amount` conform flag-ului price_include al taxelor
            # (compute_all pe aceleași taxe). Pentru taxe „TVA inclus" trimitem brutul, pentru taxe
            # „pe deasupra" (non-price-include) trimitem netul, ca subtotalul + TVA-ul să corespundă
            # exact cu cheltuiala hr.expense.
            taxes = expense.tax_ids
            price_include = bool(taxes) and all(taxes.mapped("price_include"))
            line_amount = expense.total_amount if price_include else expense.untaxed_amount
            line_model.create(
                {
                    "expenses_deduction_id": self.id,
                    "hr_expense_id": expense.id,
                    "name": expense.name,
                    "date": expense.date,
                    "amount": line_amount,
                    "tax_ids": [(6, 0, expense.tax_ids.ids)],
                    "partner_id": expense.vendor_id.id,
                    "expense_account_id": expense.account_id.id,
                    "analytic_distribution": expense.analytic_distribution,
                    "type": "expenses",
                    "currency_id": expense.currency_id.id,
                }
            )
        if expenses:
            expenses.sudo().write({"expenses_deduction_id": self.id})
        return True

    def action_open_import_hr_expenses(self):
        self.ensure_one()
        if self.state not in ("draft", "advance"):
            raise UserError(self.env._("Cheltuielile pot fi preluate doar într-un decont în starea Draft sau Advance."))
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Preia cheltuieli HR"),
            "res_model": "deltatech.expenses.import.hr",
            "view_mode": "form",
            "target": "new",
            "context": {"default_expenses_deduction_id": self.id},
        }

    def _release_imported_lines(self):
        super()._release_imported_lines()
        # eliberăm cheltuielile hr.expense preluate: ștergem liniile importate, iar override-ul
        # unlink dezleagă cheltuiala (expenses_deduction_id=False), redevenind disponibilă pentru
        # fluxul standard sau o nouă preluare. Liniile introduse manual rămân pentru re-validare.
        self.expenses_line_ids.filtered("hr_expense_id").unlink()


class DeltatechExpensesDeductionLine(models.Model):
    _inherit = "deltatech.expenses.deduction.line"

    hr_expense_id = fields.Many2one(
        "hr.expense",
        string="HR Expense",
        copy=False,
        readonly=True,
        help="Cheltuiala hr.expense din care a fost preluată această linie.",
    )

    def unlink(self):
        # eliberăm cheltuielile hr.expense preluate, ca să nu rămână blocate de la postarea standard
        linked_expenses = self.mapped("hr_expense_id")
        res = super().unlink()
        if linked_expenses:
            linked_expenses.sudo().write({"expenses_deduction_id": False})
        return res
