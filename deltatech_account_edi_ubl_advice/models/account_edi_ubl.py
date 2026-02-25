# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class AccountEdiXmlUBL20(models.AbstractModel):
    _inherit = "account.edi.xml.ubl_20"

    # class AccountEdiXmlUBLBIS3(models.AbstractModel):
    #     _inherit = "account.edi.xml.ubl_bis3"

    def _export_invoice_vals(self, invoice):
        # old helper
        vals_list = super()._export_invoice_vals(invoice)

        pickings = self.env["stock.picking"]
        for line in invoice.invoice_line_ids:
            for sale_line in line.sale_line_ids:
                for move in sale_line.move_ids:
                    if move.picking_id.state == "done":
                        pickings |= move.picking_id
        if pickings:
            names = pickings.mapped("name")
            vals_list["vals"]["despatch_advice"] = ", ".join(names)

        return vals_list

    def _export_invoice_new(self, invoice):
        res = super()._export_invoice_new(invoice)
        return res

    def _add_invoice_header_nodes(self, document_node, vals):
        res = super()._add_invoice_header_nodes(document_node, vals)
        invoice = vals["invoice"]
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

    def _get_document_template(self, vals):
        res = super()._get_document_template(vals)
        if vals["document_type"] == "invoice":
            res["cac:DespatchDocumentReference"] = {"cbc:ID": {}}
        return res

    def _add_invoice_delivery_nodes(self, document_node, vals):
        res = super()._add_invoice_delivery_nodes(document_node, vals)

        return res
