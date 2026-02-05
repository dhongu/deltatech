# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.fields import Domain


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    doc_count = fields.Integer(string="Number of documents attached", compute="_compute_attached_docs_count")

    def get_attachment_domain(self):
        domain = [("res_model", "=", "purchase.order"), ("res_id", "=", self.id)]

        # In unele instalații, legătura dintre PO și picking poate fi prin câmpul purchase_id
        # (nu doar prin picking_ids). Pentru robustețe, agregăm ambele surse.
        pickings = self.picking_ids
        # include explicit toate pickings legate prin purchase_id
        extra_pickings = self.env["stock.picking"].search([("purchase_id", "=", self.id)])
        if extra_pickings:
            pickings |= extra_pickings

        if pickings:
            subdomains = [
                ("res_model", "=", "stock.picking"),
                ("res_id", "in", pickings.ids),
            ]
            domain = Domain.OR([subdomains, domain])
        if self.invoice_ids:
            subdomains = [
                ("res_model", "=", "account.move"),
                ("res_id", "in", self.invoice_ids.ids),
            ]
            domain = Domain.OR([subdomains, domain])
        return domain

    def _compute_attached_docs_count(self):
        for order in self:
            domain = order.get_attachment_domain()
            order.doc_count = self.env["ir.attachment"].search_count(domain)

    def attachment_tree_view(self):
        domain = self.get_attachment_domain()
        return {
            "name": self.env._("Attachments"),
            "domain": domain,
            "res_model": "ir.attachment",
            "type": "ir.actions.act_window",
            "view_id": False,
            "view_mode": "kanban,list,form",
            "context": f"{{'default_res_model': '{self._name}','default_res_id': {self.id}}}",
        }
