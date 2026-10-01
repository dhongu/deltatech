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
                # amount_max is gone in 20; the wizard shows what is already paid
                "amount_paid": self.payment_amount,
            }
        )

        return {
            "type": "ir.actions.act_url",
            "url": payment_link.link,
            "target": "new",
        }

    def _payment_to_order_currency(self, amount, currency, date):
        """Suma platita intr-o alta moneda, la cursul de la data documentului."""
        self.ensure_one()
        if not currency or currency == self.currency_id:
            return amount
        return currency._convert(
            amount, self.currency_id, self.company_id, date or self.date_order or fields.Date.context_today(self)
        )

    @api.depends(
        "amount_total",
        "currency_id",
        "transaction_ids.state",
        "transaction_ids.amount",
        "transaction_ids.provider_id",
        "transaction_ids.currency_id",
        "invoice_ids.state",
        "invoice_ids.currency_id",
        "invoice_ids.amount_residual",
        "invoice_ids.amount_total",
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

            # Aceiasi bani pot fi vazuti de doua ori: ca tranzactie confirmata si ca suma incasata
            # pe factura. O tranzactie fara plata contabila (provider fara jurnal, ex. card Shopify)
            # ajunge pe factura abia la reconcilierea decontarii, deci nu se poate sti din date daca
            # e deja inclusa. Se ia maximul celor doua surse: nu dubleaza decontarea si nici nu pierde
            # tranzactia inca nedecontata (card 382 + link 44 cu plata pe factura -> 426).
            # Toate sumele se aduc in moneda comenzii: *_signed de pe factura sunt in moneda companiei
            # si, la o comanda in valuta, comparate cu amount_total ar da o comanda platita partial
            # drept platita integral.
            invoice_paid = sum(
                order._payment_to_order_currency(
                    (invoice.amount_total - invoice.amount_residual) * (1 if invoice.is_inbound() else -1),
                    invoice.currency_id,
                    invoice.invoice_date,
                )
                for invoice in order.invoice_ids.filtered(lambda a: a.state == "posted")
            )
            transaction_paid = sum(
                order._payment_to_order_currency(tx.amount, tx.currency_id, tx.last_state_change) for tx in done_tx
            )
            amount_paid = max(0.0, invoice_paid, transaction_paid)
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
