# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.fields import Domain


class StockPicking(models.Model):
    _inherit = "stock.picking"

    doc_count = fields.Integer(string="Number of documents attached", compute="_compute_attached_docs_count")

    def get_attachment_domain(self):
        picking = self
        domain = [("res_model", "=", "stock.picking"), ("res_id", "=", picking.id)]
        invoice_ids = []
        if picking.sale_id:
            subdomains = [
                ("res_model", "=", "sale.order"),
                ("res_id", "=", picking.sale_id.id),
            ]
            domain = Domain.OR([subdomains, domain])
            subdomains = [("id", "in", picking.sale_id.invoice_ids.message_main_attachment_id.ids)]
            domain = Domain.OR([subdomains, domain])
            invoice_ids += picking.sale_id.sudo().invoice_ids.ids
        if picking.purchase_id:
            subdomains = [
                ("res_model", "=", "purchase.order"),
                ("res_id", "=", picking.purchase_id.id),
            ]
            domain = Domain.OR([subdomains, domain])
            subdomains = [("id", "in", picking.sale_id.invoice_ids.message_main_attachment_id.ids)]
            domain = Domain.OR([subdomains, domain])
            invoice_ids += picking.purchase_id.sudo().invoice_ids.ids
        if invoice_ids:
            subdomains = [
                ("res_model", "=", "account.move"),
                ("res_id", "=", invoice_ids),
            ]
            domain = Domain.OR([subdomains, domain])

        return domain

    def _compute_attached_docs_count(self):
        for picking in self:
            domain = picking.get_attachment_domain()
            picking.doc_count = self.env["ir.attachment"].search_count(domain)

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
