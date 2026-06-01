# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import UserError


class ExpensesImportHr(models.TransientModel):
    _name = "deltatech.expenses.import.hr"
    _description = "Import HR Expenses into Expenses Deduction"

    expenses_deduction_id = fields.Many2one(
        "deltatech.expenses.deduction",
        string="Expenses Deduction",
        ondelete="cascade",
    )
    employee_id = fields.Many2one("hr.employee", string="Employee", readonly=True)
    expense_ids = fields.Many2many("hr.expense", string="Expenses")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ctx = self.env.context
        # Direcția 1: deschis dintr-un decont -> preîncarcă cheltuielile eligibile ale angajatului
        deduction_id = ctx.get("default_expenses_deduction_id") or (
            ctx.get("active_model") == "deltatech.expenses.deduction" and ctx.get("active_id")
        )
        if deduction_id:
            deduction = self.env["deltatech.expenses.deduction"].browse(deduction_id)
            res["expenses_deduction_id"] = deduction.id
            res["employee_id"] = deduction.employee_id.id
            res["expense_ids"] = [(6, 0, deduction._eligible_hr_expenses().ids)]
        # Direcția 2: deschis din lista de cheltuieli -> selecția devine conținutul, decontul se alege
        elif ctx.get("active_model") == "hr.expense" and ctx.get("active_ids"):
            expenses = self.env["hr.expense"].browse(ctx["active_ids"]).filtered(lambda e: not e.expenses_deduction_id)
            employees = expenses.employee_id
            if len(employees) > 1:
                raise UserError(self.env._("Selectați cheltuieli ale aceluiași angajat."))
            res["employee_id"] = employees.id
            res["expense_ids"] = [(6, 0, expenses.ids)]
        return res

    def action_import(self):
        self.ensure_one()
        if not self.expenses_deduction_id:
            raise UserError(self.env._("Selectați decontul de cheltuieli în care se preiau cheltuielile."))
        self.expenses_deduction_id._import_hr_expenses(self.expense_ids)
        return {"type": "ir.actions.act_window_close"}
