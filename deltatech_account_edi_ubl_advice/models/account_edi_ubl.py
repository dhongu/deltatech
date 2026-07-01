# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class AccountEdiXmlUBLBis3(models.AbstractModel):
    # Extindem la nivelul ubl_bis3, nu ubl_20: în Odoo 19 metoda
    # _add_invoice_header_nodes din ubl_bis3 este un OVERRIDE care NU apelează
    # super(), deci un patch pe ubl_20 nu mai este niciodată executat pentru
    # e-Factura RO (account.edi.xml.ubl_ro -> ubl_bis3). Ne agățăm de ubl_bis3,
    # care este baza folosită la exportul CIUS-RO.
    _inherit = "account.edi.xml.ubl_bis3"

    def _add_invoice_header_nodes(self, document_node, vals):
        super()._add_invoice_header_nodes(document_node, vals)
        invoice = vals["invoice"]
        if invoice.move_type != "out_invoice":
            return
        if "sale_line_ids" not in invoice.invoice_line_ids._fields:
            return
        pickings = self.env["stock.picking"]
        for line in invoice.invoice_line_ids:
            for sale_line in line.sale_line_ids:
                for move in sale_line.move_ids:
                    if move.picking_id.state == "done":
                        pickings |= move.picking_id
        if pickings:
            names = pickings.mapped("name")
            vals["despatch_advice"] = ", ".join(names)
            # Nodul este definit în template-ul Invoice (cac:DespatchDocumentReference,
            # între BillingReference și Delivery), deci ordinea în XML este corectă
            # indiferent de momentul inserării în dict.
            document_node["cac:DespatchDocumentReference"] = {"cbc:ID": {"_text": ", ".join(names)}}
