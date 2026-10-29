# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class DeltatechExpensesDeductionAllocation(models.Model):
    """Factura furnizorului stinsă de o plată directă din avans (linie „Supplier Payment") și suma
    alocată ei. La validarea decontului, fiecare alocare are linia ei Dr 401 în nota Dr 401 = Cr 542,
    reconciliată doar cu factura aleasă."""

    _name = "deltatech.expenses.deduction.allocation"
    _description = "Expenses Deduction Supplier Payment Allocation"
    _order = "line_id, id"
    _check_company_auto = True

    # o factură apare o singură dată pe linie: suma ei alocată se compară cu restul de plată
    _line_bill_uniq = models.Constraint(
        "unique(line_id, move_id)",
        "A bill can be allocated only once on a supplier payment line.",
    )

    line_id = fields.Many2one(
        "deltatech.expenses.deduction.line", string="Expenses Line", required=True, ondelete="cascade", index=True
    )
    expenses_deduction_id = fields.Many2one(related="line_id.expenses_deduction_id", store=True, index=True)
    company_id = fields.Many2one(related="line_id.expenses_deduction_id.company_id", store=True)
    commercial_partner_id = fields.Many2one(related="line_id.partner_id.commercial_partner_id")
    currency_id = fields.Many2one(related="line_id.currency_id")
    move_id = fields.Many2one(
        "account.move",
        string="Bill",
        required=True,
        check_company=True,
        domain="[('move_type', 'in', ('in_invoice', 'in_receipt')), ('state', '=', 'posted'), "
        "('payment_state', 'in', ('not_paid', 'partial')), ('company_id', '=', company_id), "
        "('commercial_partner_id', '=', commercial_partner_id)]",
    )
    bill_currency_id = fields.Many2one(related="move_id.currency_id", string="Bill Currency")
    invoice_date_due = fields.Date(related="move_id.invoice_date_due")
    bill_amount_residual = fields.Monetary(
        related="move_id.amount_residual", currency_field="bill_currency_id", string="Amount Due"
    )
    amount = fields.Monetary(string="Allocated Amount", help="Amount of the payment that settles this bill.")
    state = fields.Selection(related="line_id.state")

    def _bill_residual(self, date):
        """Restul de plată al facturii în moneda decontului (la cursul din `date` dacă monedele diferă)."""
        self.ensure_one()
        bill = self.move_id
        if bill.currency_id == self.currency_id:
            return bill.amount_residual
        company = bill.company_id
        return company.currency_id._convert(
            abs(bill.amount_residual_signed), self.currency_id, company, date or fields.Date.context_today(self)
        )

    @api.constrains("line_id")
    def _check_line_type(self):
        self.line_id._check_allocation_type()

    @api.onchange("move_id")
    def _onchange_move_id(self):
        """Implicit, restul de plată al facturii, fără să depășească suma încă nealocată a plății."""
        if not self.move_id:
            return
        line = self.line_id
        residual = self._bill_residual(line.date)
        free = line._supplier_payment_amount() - sum((line.allocation_ids - self).mapped("amount"))
        self.amount = min(residual, free) if self.currency_id.compare_amounts(free, 0.0) > 0 else residual

    @api.model_create_multi
    def create(self, vals_list):
        lines = self.env["deltatech.expenses.deduction.line"].browse(
            [vals["line_id"] for vals in vals_list if vals.get("line_id")]
        )
        lines._check_deduction_open(lines.mapped("expenses_deduction_id"))
        return super().create(vals_list)

    def write(self, vals):
        self.line_id._check_deduction_open(self.mapped("expenses_deduction_id"))
        return super().write(vals)

    def unlink(self):
        self.line_id._check_deduction_open(self.mapped("expenses_deduction_id"))
        return super().unlink()
