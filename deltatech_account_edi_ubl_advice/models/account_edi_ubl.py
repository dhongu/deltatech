# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class AccountEdiXmlUBL20(models.AbstractModel):
    _inherit = "account.edi.xml.ubl_20"

    def _add_invoice_header_nodes(self, document_node, vals):
        res = super()._add_invoice_header_nodes(document_node, vals)
        invoice = vals["invoice"]
        if invoice.move_type != "out_invoice":
            return res
        if "sale_line_ids" not in invoice.invoice_line_ids._fields:
            return res
        pickings = self.env["stock.picking"]
        for line in invoice.invoice_line_ids:
            for sale_line in line.sale_line_ids:
                for move in sale_line.move_ids:
                    if move.picking_id.state == "done":
                        pickings |= move.picking_id
        if pickings:
            names = pickings.mapped("name")
            vals["despatch_advice"] = ", ".join(names)
            document_node["cac:DespatchDocumentReference"] = {"cbc:ID": {"_text": ", ".join(names)}}
        return res
