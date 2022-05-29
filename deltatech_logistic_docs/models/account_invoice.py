# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, fields, models
from odoo.osv import expression


class AccountInvoice(models.Model):
    _inherit = "account.move"

    doc_count = fields.Integer(string="Number of documents attached", compute="_compute_attached_docs_count")

    def get_attachment_domain(self):

        domain = [("res_model", "=", "account.move"), ("res_id", "=", self.id)]
        if self.is_invoice():
            sale_orders = self.env["sale.order"]
            purchase_orders = self.env["purchase.order"]
            pickings = self.env["stock.picking"]

            for line in self.invoice_line_ids:
                for sale_line in line.sale_line_ids:
                    sale_orders |= sale_line.order_id
                purchase_orders |= line.purchase_order_id

            pickings |= sale_orders.mapped("picking_ids")
            pickings |= purchase_orders.mapped("picking_ids")

            if sale_orders:
                subdomains = [("res_model", "=", "sale.order"), ("res_id", "in", sale_orders.ids)]
                domain = expression.OR([subdomains, domain])
            if purchase_orders:
                subdomains = [("res_model", "=", "purchase.order"), ("res_id", "in", purchase_orders.ids)]
                domain = expression.OR([subdomains, domain])

            if pickings:
                subdomains = [("res_model", "=", "stock.picking"), ("res_id", "in", pickings.ids)]
                domain = expression.OR([subdomains, domain])

        return domain

    def _compute_attached_docs_count(self):
        for invoice in self:
            domain = invoice.get_attachment_domain()
            invoice.doc_count = self.env["ir.attachment"].search_count(domain)

    def attachment_tree_view(self):
        domain = self.get_attachment_domain()
        return {
            "name": _("Attachments"),
            "domain": domain,
            "res_model": "ir.attachment",
            "type": "ir.actions.act_window",
            "view_id": False,
            "view_mode": "kanban,tree,form",
            "context": "{{'default_res_model': '{}','default_res_id': {}}}".format(self._name, self.id),
        }
