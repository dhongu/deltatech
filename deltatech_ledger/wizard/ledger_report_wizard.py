from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Domain


class LedgerReportWizard(models.TransientModel):
    _name = "ledger.report.wizard"
    _description = "Print Ledger"

    date_from = fields.Date(
        string="From", required=True, default=lambda self: fields.Date.context_today(self).replace(month=1, day=1)
    )
    date_to = fields.Date(string="To", required=True, default=fields.Date.context_today)
    record_type = fields.Selection([("entry", "Entry"), ("exit", "Exit")], string="Record Type")
    include_canceled = fields.Boolean(string="Include Canceled", default=True)
    include_undated = fields.Boolean(
        string="Include Undated Reservations", default=True, help="Reserved numbers that have no date yet."
    )
    company_id = fields.Many2one("res.company", string="Company", required=True, default=lambda self: self.env.company)

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for wiz in self:
            if wiz.date_from > wiz.date_to:
                raise UserError(self.env._("The start date must not be after the end date."))

    def action_print(self):
        self.ensure_one()
        date_domain = Domain([("record_date", ">=", self.date_from), ("record_date", "<=", self.date_to)])
        if self.include_undated:
            # an undated reservation has no date, so it is shown for the years of its number
            date_domain |= Domain(
                [
                    ("record_date", "=", False),
                    ("sequence_year", ">=", self.date_from.year),
                    ("sequence_year", "<=", self.date_to.year),
                ]
            )
        domain = Domain("company_id", "=", self.company_id.id) & date_domain
        if self.record_type:
            domain &= Domain("record_type", "=", self.record_type)
        if not self.include_canceled:
            domain &= Domain("state", "!=", "canceled")
        records = self.env["ledger.ledger"].search(domain, order="name")
        if not records:
            raise UserError(self.env._("There are no records for the selected period."))
        data = {
            "date_from": fields.Date.to_string(self.date_from),
            "date_to": fields.Date.to_string(self.date_to),
            "company_name": self.company_id.name,
        }
        return self.env.ref("deltatech_ledger.action_report_ledger").report_action(records, data=data)
