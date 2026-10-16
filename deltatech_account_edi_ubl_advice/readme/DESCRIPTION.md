# Deltatech UBL Despatch Advice

This module enriches outgoing UBL e-invoices (e-Factura) with a reference to the
delivery documents behind each invoice.

When a customer invoice is generated as UBL, the module looks up the validated
deliveries (`stock.picking` in the *done* state) linked to the invoice lines
through their sale order lines, and adds their references to the invoice XML as a
`cac:DespatchDocumentReference` node.

This way the recipient can trace, directly from the electronic invoice, which
delivery notes (despatch advices) the invoice covers.

## Key Features

- Adds `cac:DespatchDocumentReference` to outgoing UBL invoices.
- Collects delivery references automatically from linked, validated pickings.
- Works transparently on top of the standard UBL/CII e-invoice export — no extra
  configuration required.

## Requirements

- Depends on `account_edi_ubl_cii` (standard Odoo UBL/CII e-invoicing).
- Deliveries must be linked to the invoice through sale order lines (Sales flow).
