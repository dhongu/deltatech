# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, fields, models
from odoo.osv import expression


class StockPicking(models.Model):
    _inherit = "stock.picking"

    doc_count = fields.Integer(string="Number of documents attached", compute="_compute_attached_docs_count")

    def get_attachment_domain(self):
        picking = self
        domain = [("res_model", "=", "stock.picking"), ("res_id", "=", picking.id)]
        if picking.sale_id:
            subdomains = [("res_model", "=", "sale.order"), ("res_id", "=", picking.sale_id.id)]
            domain = expression.OR([subdomains, domain])
        if picking.purchase_id:
            subdomains = [("res_model", "=", "purchase.order"), ("res_id", "=", picking.purchase_id.id)]
            domain = expression.OR([subdomains, domain])
        return domain

    def _compute_attached_docs_count(self):
        for picking in self:
            domain = picking.get_attachment_domain()
            picking.doc_count = self.env["ir.attachment"].search_count(domain)

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
