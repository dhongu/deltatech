# -*- coding: utf-8 -*-
# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import time

from odoo import models, fields, api, _
from odoo.exceptions import except_orm
from odoo.tools import DEFAULT_SERVER_TIME_FORMAT
from odoo.exceptions import UserError, RedirectWarning


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def action_move_create(self):
        # inainte de a face notele contabile trebuie sa verifica daca toate pozitiile din factura de achizitie
        # sunt legate de o comanda de aprovizonaoare
        if self.env.context.get('create_purchase_and_receipt',False):
            purchase_invoices = self.filtered(lambda inv: inv.type == 'in_invoice')
            purchase_invoices.add_to_purchase()
            purchase_invoices.receipt_to_stock()
        return super(AccountInvoice, self).action_move_create()

    @api.multi
    def add_to_purchase(self):
        """
            Verifica daca toate pozitiile din factura de achizitie se regasesc intr-o comanda de achizitie.
            sunt 2 variante: sa caut o comanda de aprovizonare
                                sau sa fac o comanda noua.
        """

        for invoice in self:
            if not invoice.date_invoice:
                raise UserError(_("Please enter invoice date"))
            # exista o comanda de achizitie legata de aceasta factura ?
            purchase_order = self.env['purchase.order']
            for line in invoice.invoice_line_ids:
                purchase_order |= line.purchase_id

            # am gasit linii care nu sunt in comanda de achizitie
            lines_without_purchase = invoice.invoice_line_ids.filtered(lambda line: not line.purchase_line_id)
            if lines_without_purchase:
                # trebuie sa verific daca sunt produse stocabile ?

                if len(purchase_order) != 1:
                    purchase_order = self.env['purchase.order'].create({
                        'partner_id': invoice.partner_id.id,
                        'date_order': invoice.date_invoice,
                        'partner_ref': invoice.reference,
                        'fiscal_position_id': invoice.fiscal_position_id.id,
                        'from_invoice_id': invoice.id,
                        'currency_id': invoice.currency_id.id,  # Preluare Moneda in comanda de achizitie
                    })

                for line in lines_without_purchase:
                    line_po = self.env['purchase.order.line'].create({
                        'order_id': purchase_order.id,
                        'date_planned': invoice.date_invoice,
                        'sequence': line.sequence,
                        'product_id': line.product_id.id,
                        'product_uom': line.uom_id.id,
                        'name': line.name,
                        'price_unit': line.price_unit,
                        'product_qty': line.quantity,
                        'discount': line.discount,
                        'taxes_id': [(6, 0, line.invoice_line_tax_ids.ids)]
                    })
                    line.write({
                        'purchase_line_id': line_po.id,
                        'purchase_id': purchase_order.id,
                    })
                if purchase_order.from_invoice_id:
                    purchase_order.button_confirm()  # confirma comanda de achizitie
                    purchase_order.message_post_with_view('mail.message_origin_link',
                                                          values={'self': purchase_order, 'origin': invoice},
                                                          subtype_id=self.env.ref('mail.mt_note').id)
                    link = "<a href=# data-oe-model=purchase.order data-oe-id=" + str(
                        purchase_order.id) + ">" + purchase_order.name + "</a>"
                    message = _("The purchase order %s was generated.") % link
                    invoice.message_post(body=message)
                    if not invoice.origin:
                        invoice.write({
                            'origin': purchase_order.name
                        })

    @api.multi
    def receipt_to_stock(self):
        purchase_orders = self.env['purchase.order']
        for invoice in self:
            # trebuie sa determin care este cantitatea care trebuie sa fie receptionata
            for line in invoice.invoice_line_ids:
                purchase_orders |= line.purchase_id
        # doar pentru comenzile fenerate din factura se face receptia
        purchase_orders.filtered(lambda order: order.from_invoice_id).receipt_to_stock()
