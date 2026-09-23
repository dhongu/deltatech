# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Stored, so the order list can be filtered, grouped and sorted on them in SQL
    provider_id = fields.Many2one("payment.provider", compute="_compute_payment", store=True)
    payment_amount = fields.Monetary(string="Amount Payment", compute="_compute_payment", store=True)

    payment_status = fields.Selection(
        [
            ("without", "Without"),
            ("initiated", "Initiated"),
            ("authorized", "Authorized"),
            ("partial", "Partial"),
            ("done", "Done"),
            ("pending", "Pending"),
            ("cancelled", "Cancelled"),
        ],
        default="without",
        compute="_compute_payment",
        store=True,
    )

    def action_payment_link(self):
        payment_link = self.env["payment.link.wizard"].create(
            {
                "res_id": self.id,
                "res_model": "sale.order",
                # what is still to be paid on the order, whatever was paid through
                # transactions or directly on its invoices
                "amount": max(0.0, self.amount_total - self.payment_amount),
                "currency_id": self.currency_id.id,
                "partner_id": self.partner_id.id,
                "amount_max": self.amount_total,
            }
        )

        return {
            "type": "ir.actions.act_url",
            "url": payment_link.link,
            "target": "new",
        }

    @api.depends(
        "amount_total",
        "currency_id",
        "transaction_ids.state",
        "transaction_ids.amount",
        "transaction_ids.provider_id",
        "invoice_ids.state",
        "invoice_ids.payment_state",
        "invoice_ids.amount_residual_signed",
        "invoice_ids.amount_total_signed",
        "invoice_ids.transaction_ids.is_post_processed",
        "invoice_ids.transaction_ids.payment_id",
    )
    def _compute_payment(self):
        for order in self:
            # filtrează tranzacțiile NewId (din onchange) înainte de sortare, ca să evităm
            # TypeError la compararea NewId cu int
            all_tx = order.sudo().transaction_ids.filtered(lambda t: isinstance(t.id, int)).sorted("id")
            done_tx = all_tx.filtered(lambda t: t.state == "done")
            authorized_tx = all_tx.filtered(lambda t: t.state == "authorized")
            pending_tx = all_tx.filtered(lambda t: t.state == "pending")
            cancel_tx = all_tx.filtered(lambda t: t.state == "cancel")

            counted_tx = done_tx
            amount_paid = 0.0
            for invoice in order.invoice_ids.filtered(lambda a: a.state == "posted"):
                amount_invoice = invoice.amount_total_signed - invoice.amount_residual_signed
                if amount_invoice:
                    amount_paid += amount_invoice
                    # se scad doar tranzactiile care au generat plata in contabilitate: suma lor e deja
                    # in `amount_invoice`. O tranzactie post-procesata fara plata (ex. provider fara jurnal,
                    # comenzi importate din marketplace) nu apare in factura si trebuie numarata separat.
                    counted_tx -= invoice.sudo().transaction_ids.filtered(
                        lambda a: a.is_post_processed and a.payment_id
                    )
            amount_paid = max(0.0, amount_paid + sum(counted_tx.mapped("amount")))
            order.payment_amount = amount_paid

            # Status — ordinea contează: authorized > pending > cancelled > initiated
            if amount_paid and order.currency_id.compare_amounts(amount_paid, order.amount_total) >= 0:
                status = "done"
            elif amount_paid:
                status = "partial"
            elif not all_tx:
                status = "without"
            elif authorized_tx:
                status = "authorized"
            elif pending_tx:
                status = "pending"
            elif cancel_tx:
                status = "cancelled"
            else:
                status = "initiated"  # draft / error
            order.payment_status = status

            # Procesatorul afișat: al celei mai relevante tranzacții, cea mai recentă din grup
            for group in (done_tx, authorized_tx, pending_tx, cancel_tx, all_tx):
                if group:
                    order.provider_id = group[-1].provider_id
                    break
            else:
                order.provider_id = self.env["payment.provider"]
