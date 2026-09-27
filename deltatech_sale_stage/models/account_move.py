# ©  2015-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        # faza „facturat” a comenzii se setează la validarea facturii, când comanda
        # a ajuns complet facturată (sale.order._get_invoice_status nu există în core)
        posted = super()._post(soft)
        orders = posted.filtered(lambda move: move.is_invoice()).line_ids.sale_line_ids.order_id
        orders.filtered(lambda order: order.invoice_status == "invoiced").set_phase("invoiced")
        return posted
