# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    expenses_deduction_count = fields.Integer(
        string="Expenses Deductions",
        compute="_compute_expenses_deduction_count",
    )

    def _compute_expenses_deduction_count(self):
        deduction = self.env["deltatech.expenses.deduction"]
        data = deduction._read_group(
            [("employee_id", "in", self.ids)],
            groupby=["employee_id"],
            aggregates=["__count"],
        )
        mapped_count = {employee.id: count for employee, count in data}
        for employee in self:
            employee.expenses_deduction_count = mapped_count.get(employee.id, 0)

    def action_open_expenses_deductions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Expenses Deductions"),
            "res_model": "deltatech.expenses.deduction",
            "view_mode": "list,form",
            "domain": [("employee_id", "=", self.id)],
            "context": {"default_employee_id": self.id},
        }
