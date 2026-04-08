from odoo import models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    def action_view_products(self):
        action = self.env["ir.actions.actions"]._for_xml_id("product.product_template_action")
        pids = []
        for line in self.invoice_line_ids:
            if line.product_id:
                pids.append(line.product_id.product_tmpl_id.id)
        action["domain"] = [("id", "in", pids)]
        return action
