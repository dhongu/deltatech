# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Doar acțiuni, fără câmpuri: comanda nu primește nimic stocat de la acest modul.

    def action_card_payment(self):
        self.ensure_one()
        return self.env["deltatech.card.payment"]._open_for(self)

    def action_view_card_receipts(self):
        self.ensure_one()
        return self.env["deltatech.expected.receipt"]._action_for_domain([("sale_order_id", "=", self.id)])
