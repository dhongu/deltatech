from odoo import api, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange("journal_id")
    def _onchange_journal_id(self):
        result = super()._onchange_journal_id()
        message = self.check_data(
            journal_id=self.journal_id.id,
            invoice_date=self.invoice_date,
        )
        if message:
            return {
                "warning": {
                    "title": self.env._("Warning"),
                    "message": message,
                }
            }
        return result

    def action_post(self):
        """Prevent customer invoices from being posted out of date order."""
        for move in self:
            if move.journal_id.restrict_date:
                message = move.check_data()
                if message:
                    raise UserError(message)
        return super().action_post()

    def action_get_number(self):
        for invoice in self:
            if not invoice.invoice_date:
                raise UserError(self.env._("The invoice has no date."))

            message = invoice.check_data()
            if message:
                raise UserError(message)

            sequence = invoice.journal_id.journal_sequence_id
            if not sequence:
                raise UserError(self.env._("Please define a sequence on the journal."))

            invoice.name = sequence.with_context(
                ir_sequence_date=invoice.invoice_date,
            ).next_by_id()
        return True

    def check_data(self, journal_id=None, invoice_date=None):
        for invoice in self:
            journal = self.env["account.journal"].browse(journal_id or invoice.journal_id.id)
            checked_date = invoice_date or invoice.invoice_date
            if (
                journal.restrict_date
                and checked_date
                and invoice.move_type in ("out_invoice", "out_refund")
                and invoice.state == "draft"
            ):
                later_invoice = self.search(
                    [
                        ("move_type", "=", invoice.move_type),
                        ("invoice_date", ">", checked_date),
                        ("journal_id", "=", journal.id),
                        ("state", "=", "posted"),
                    ],
                    limit=1,
                    order="invoice_date desc",
                )
                if later_invoice:
                    return self.env._(
                        "Post the invoice with a date on or after %s",
                        later_invoice.invoice_date,
                    )
        return ""

    def action_number(self):
        """Synchronize the document reference after a manual renumbering."""
        for invoice in self:
            if invoice.move_type in ("in_invoice", "in_refund"):
                reference = invoice.ref or invoice.name
            else:
                reference = invoice.name
                invoice.ref = reference
            invoice.line_ids.write({"ref": reference})
        return True
