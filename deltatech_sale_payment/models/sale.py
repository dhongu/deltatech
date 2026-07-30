# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.fields import Domain


class SaleOrder(models.Model):
    _inherit = "sale.order"

    provider_id = fields.Many2one("payment.provider", compute="_compute_payment")
    payment_amount = fields.Monetary(string="Amount Payment", compute="_compute_payment")

    payment_status = fields.Selection(
        [
            ("without", "Without"),
            ("initiated", "Initiated"),
            ("authorized", "Authorized"),
            ("partial", "Partial"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        default="without",
        compute="_compute_payment",
        search="_search_payment_status",
    )

    def action_payment_link(self):
        payment_link = self.env["payment.link.wizard"].create(
            {
                "res_id": self.id,
                "res_model": "sale.order",
                "amount": self.amount_total - sum(self.invoice_ids.mapped("amount_total")),
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

    @api.depends("transaction_ids", "transaction_ids.state")
    def _compute_payment(self):
        for order in self:
            amount = 0
            payment_status = "without"

            provider = self.env["payment.provider"]
            # filtrează tranzacțiile NewId (din onchange) înainte de sortare, ca să evităm
            # TypeError la compararea NewId cu int
            all_transactions = order.sudo().transaction_ids.filtered(lambda t: isinstance(t.id, int)).sorted("id")
            if all_transactions:
                provider = all_transactions[-1].provider_id

            transactions = all_transactions.filtered(lambda a: a.state == "done")

            for invoice in order.invoice_ids.filtered(lambda a: a.state == "posted"):
                amount_invoice = invoice.amount_total_signed - invoice.amount_residual_signed
                if amount_invoice:
                    amount += amount_invoice
                    transactions = transactions - invoice.sudo().transaction_ids.filtered(lambda a: a.is_post_processed)

            for transaction in transactions:
                amount += transaction.amount
                provider = transaction.provider_id

            order.payment_amount = amount
            if amount:
                if amount < order.amount_total:
                    payment_status = "partial"
                else:
                    payment_status = "done"

            if not amount:
                payment_status = "without"
                if all_transactions:
                    payment_status = "initiated"

                    cancel_tx = all_transactions.filtered(lambda t: t.state == "cancel")
                    if cancel_tx:
                        payment_status = "cancelled"

                    for transaction in all_transactions.sorted(lambda a: a.id):
                        provider = transaction.provider_id

                    authorized_transaction_ids = all_transactions.filtered(lambda t: t.state == "authorized")
                    if authorized_transaction_ids:
                        payment_status = "authorized"
                        for transaction in authorized_transaction_ids:
                            provider = transaction.provider_id

            order.payment_status = payment_status
            order.provider_id = provider

    def _search_payment_status(self, operator, value):
        # Odoo 19 rescrie `=` / `!=` in `in` / `not in` peste o colectie de valori
        # (_operator_equal_as_in din odoo/orm/domains.py), la nivel BASIC, inaintea
        # expandarii metodei `search`: metoda nu primeste niciodata operatorul `=`
        if operator not in ("in", "not in"):
            return NotImplemented
        if operator == "in":
            return Domain.OR(self._get_payment_status_domain(status) for status in value)
        return Domain.AND(~self._get_payment_status_domain(status) for status in value)

    def _get_payment_status_domain(self, status):
        """Domeniul comenzilor cu statusul de plata dat.

        Statusurile se exclud reciproc, in aceeasi ordine de prioritate ca in
        `_compute_payment`. Ca si inainte, cautarea ia in calcul doar tranzactiile
        de plata: sumele incasate direct pe facturi nu se pot exprima in domeniu.
        """
        has_transaction = Domain("transaction_ids", "!=", False)
        has_done = Domain("transaction_ids.state", "in", ["done"])
        has_authorized = Domain("transaction_ids.state", "in", ["authorized"])
        has_cancelled = Domain("transaction_ids.state", "in", ["cancel"])
        if status == "without":
            return ~has_transaction
        if status == "initiated":
            return has_transaction & ~has_done & ~has_authorized & ~has_cancelled
        if status == "authorized":
            return has_authorized & ~has_done
        if status == "cancelled":
            return has_cancelled & ~has_authorized & ~has_done
        if status in ("partial", "done"):
            return Domain("id", "in", self._get_paid_order_ids(status))
        return Domain.FALSE

    def _get_paid_order_ids(self, status):
        """Comenzile `partial` / `done`, evaluate in Python.

        Diferenta dintre `partial` si `done` este suma incasata comparata cu totalul
        comenzii, care nu se poate exprima in domeniu; restrangem la comenzile cu
        tranzactii confirmate si evaluam statusul pe ele (ca `account.account._search_used`).
        """
        orders = self.search([("transaction_ids.state", "in", ["done"])])
        return orders.filtered(lambda order: order.payment_status == status).ids
