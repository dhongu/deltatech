# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, models
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = "account.move"

    @api.onchange("journal_id")
    def _onchange_journal_id(self):
        msg = self.check_data(journal_id=self.journal_id.id, invoice_date=self.invoice_date)
        if msg != "":
            res = {"warning": {"title": _("Warning"), "message": msg}}
            return res

    # todo: numerotarea nu se mai face in functie de secventa din jurnal
    def action_get_number(self):
        for invoice in self:
            # if invoice.name and invoice.name != "/":
            #     raise UserError(_("The invoice is already numbered."))
            if not invoice.invoice_date:
                raise UserError(_("The invoice has no date."))
            msg = self.check_data()
            if msg != "":
                raise UserError(msg)
            journal = invoice.journal_id
            if journal.journal_sequence_id:
                # If invoice is actually refund and journal has a refund_sequence then use that one or use the regular one
                sequence = journal.journal_sequence_id
                # if invoice and invoice.move_type in ["out_refund", "in_refund"] and journal.refund_sequence:
                #     if not journal.refund_sequence_id:
                #         raise UserError(_("Please define a sequence for the refunds"))
                #     sequence = journal.refund_sequence_id

                new_name = sequence.with_context(ir_sequence_date=invoice.invoice_date).next_by_id()
            else:
                raise UserError(_("Please define a sequence on the journal."))
            invoice.write({"name": new_name})

    def check_data(self, journal_id=None, invoice_date=None):

        for obj_inv in self:
            inv_type = obj_inv.move_type

            invoice_date = invoice_date or obj_inv.invoice_date
            journal_id = journal_id or obj_inv.journal_id.id

            if (inv_type == "out_invoice" or inv_type == "out_refund") and obj_inv.state == "draft":
                res = self.search(
                    [
                        ("move_type", "=", inv_type),
                        ("invoice_date", ">", invoice_date),
                        ("journal_id", "=", journal_id),
                        ("state", "=", "posted"),
                    ],
                    limit=1,
                    order="invoice_date desc",
                )
                if res:
                    invoice_date = res.invoice_date
                    return _("Post the invoice with a greater date than %s") % invoice_date
        return ""

    # def action_move_create(self):
    #     msg = self.check_data()
    #     if msg != "":
    #         raise UserError(msg)
    #     super(AccountInvoice, self).action_move_create()
    #     return True

    def action_number(self):
        # TODO: not correct fix but required a fresh values before reading it.
        self.write({})

        for inv in self:

            if inv.move_type in ("in_invoice", "in_refund"):
                if not inv.ref:
                    ref = inv.name
                else:
                    ref = inv.ref
            else:
                ref = inv.name

            self._cr.execute(
                """ UPDATE account_move SET name  = %s
                                       WHERE id=%s  """,
                (inv.name, inv.id),
            )

            self._cr.execute(
                """ UPDATE account_move SET ref = %s
                           WHERE id=%s AND (ref IS NULL OR ref = '')""",
                (ref, inv.id),
            )
            self._cr.execute(
                """ UPDATE account_move_line SET ref = %s
                           WHERE move_id=%s AND (ref IS NULL OR ref = '')""",
                (ref, inv.id),
            )
            self._cr.execute(
                """ UPDATE account_analytic_line SET ref = %s
                           FROM account_move_line
                           WHERE account_move_line.move_id = %s AND
                                 account_analytic_line.move_id = account_move_line.id""",
                (ref, inv.id),
            )
            self.invalidate_cache()

        return True
