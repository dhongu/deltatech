from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    lines = env["deltatech.expenses.deduction.line"].search(
        [("expenses_deduction_id.state", "in", ["draft", "advance"]), ("type", "=", "expenses")]
    )
    lines.filtered(lambda line: line._uses_receipt_rounding())._compute_subtotal()
