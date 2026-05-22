# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

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
                "description": self.name,
                "amount": self.amount_total
                - sum(self.invoice_ids.filtered(lambda i: i.state == "posted").mapped("amount_residual")),
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
    )
    def _compute_payment(self):
        for order in self:
            all_tx = order.sudo().transaction_ids.filtered(lambda t: isinstance(t.id, int)).sorted("id")
            done_tx = all_tx.filtered(lambda t: t.state == "done")
            authorized_tx = all_tx.filtered(lambda t: t.state == "authorized")
            cancel_tx = all_tx.filtered(lambda t: t.state == "cancel")
            pending_tx = all_tx.filtered(lambda t: t.state == "pending")

            # Facturile reconciliate complet ("paid"/"partial") se contabilizează prin
            # suma facturii; tranzacțiile lor post-procesate se elimină din done_tx
            # pentru a evita dubla numărare.
            # Facturile "in_payment" (înregistrate dar nereconciliate cu banca) NU se
            # includ în suma facturii — plata lor rămâne vizibilă prin done_tx direct.
            invoice_paid = 0.0
            for inv in order.invoice_ids.filtered(lambda i: i.state == "posted"):
                if inv.payment_state not in ("paid", "partial"):
                    continue
                paid = inv.amount_total_signed - inv.amount_residual_signed
                if paid:
                    invoice_paid += paid
                    done_tx -= inv.transaction_ids.filtered(lambda t: t.is_post_processed)

            amount_paid = max(0.0, invoice_paid + sum(done_tx.mapped("amount")))
            order.payment_amount = amount_paid

            # Status — ordinea contează: authorized suprascrie cancelled
            currency = order.currency_id
            if currency.compare_amounts(amount_paid, order.amount_total) >= 0:
                status = "done"
            elif amount_paid > 0:
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

            if done_tx:
                order.provider_id = done_tx[-1].provider_id
            elif authorized_tx:
                order.provider_id = authorized_tx[-1].provider_id
            elif pending_tx:
                order.provider_id = pending_tx[-1].provider_id
            elif cancel_tx:
                order.provider_id = cancel_tx[-1].provider_id
            elif all_tx:
                order.provider_id = all_tx[-1].provider_id
            else:
                order.provider_id = self.env["payment.provider"]

            order.payment_status = status
