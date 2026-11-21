# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    create_invoice_automatically = fields.Boolean(string="Create Invoice Automatically")
    post_invoice_automatically = fields.Boolean(
        string="Post Invoice Automatically",
        default=True,
        help="Post the customer invoices and credit notes. Vendor bills and refunds always stay in draft: "
        "they are posted when the document of the vendor arrives.",
    )
    invoice_moment = fields.Selection(
        [("cron", "Scheduled"), ("validation", "On validation")],
        string="Invoice Moment",
        default="cron",
        required=True,
        help="Scheduled: the transfers are invoiced by the scheduled action. "
        "On validation: the transfer is invoiced when it is validated; an error does not block the validation.",
    )


class StockPicking(models.Model):
    _inherit = "stock.picking"

    invoice_state = fields.Selection(
        [("to_invoice", "To Invoice"), ("invoiced", "Invoiced"), ("failed", "Failed")],
        string="Automatic Invoicing",
        copy=False,
    )
    invoice_error = fields.Text(string="Automatic Invoicing Error", copy=False, readonly=True)

    def _action_done(self):
        res = super()._action_done()
        # only the transfers of a sale or a purchase can be invoiced: the others would stay in the queue
        to_queue = self.filtered(
            lambda p: p.picking_type_id.create_invoice_automatically and (p.sale_id or p.purchase_id)
        )
        to_queue.write({"invoice_state": "to_invoice", "invoice_error": False})
        return res

    def button_validate(self):
        res = super().button_validate()
        # "On validation": invoiced here, after deltatech_invoice_picking has flagged the transfers to
        # invoice (in its button_validate), so that its flag does not override the invoice link. A transfer
        # done another way stays in the queue and the scheduled action invoices it.
        self.filtered(
            lambda p: p.state == "done"
            and p.invoice_state == "to_invoice"
            and p.picking_type_id.invoice_moment == "validation"
        )._run_auto_invoicing()
        return res

    @api.model
    def _cron_generate_invoices(self):
        pickings = self.search([("invoice_state", "=", "to_invoice")], order="id", limit=100)
        pickings._run_auto_invoicing()

    def _run_auto_invoicing(self):
        """Invoice each transfer in its own savepoint: an error rolls back only that transfer.

        The invoicing runs as superuser, on the configuration of the operation type set by the
        manager: the warehouse user validating the transfer needs no invoicing rights.
        """
        for picking in self:
            if picking.invoice_state != "to_invoice":
                continue
            try:
                with self.env.cr.savepoint():
                    picking.sudo().with_company(picking.company_id)._auto_invoice_picking()
            except Exception as error:
                _logger.exception("Error in automatic invoicing for picking %s", picking.name)
                # the savepoint was rolled back, the transaction is usable again
                message = error.args[0] if isinstance(error, UserError) and error.args else str(error)
                picking.sudo().write({"invoice_state": "failed", "invoice_error": message})

    def _auto_invoice_picking(self):
        """Invoice the quantities of this transfer, through deltatech_invoice_picking.

        - delivery of a sale: customer invoice; return from the customer: customer credit note;
        - receipt of a purchase: vendor bill in draft; return to the vendor: vendor refund in draft.
        """
        self.ensure_one()
        if self.account_move_id and not self.to_invoice:
            # already invoiced (by hand, or with another transfer)
            self.invoice_state = "invoiced"
            return
        if self.sale_id:
            invoices = self.sale_id.with_context(picking_ids=self.ids)._create_invoices(final=True)
            if self.picking_type_id.post_invoice_automatically:
                invoices.filtered(lambda i: i.state == "draft").action_post()
        elif self.purchase_id:
            # nothing left to bill would give an empty vendor bill: refuse it (deltatech_invoice_picking)
            self._check_receipts_billable()
            # the vendor bill stays in draft until the document of the vendor arrives
            self.purchase_id.with_context(receipt_picking_ids=self.ids).action_create_invoice()
        else:
            raise UserError(self.env._("The transfer has no sale or purchase order to invoice."))
        self.write({"invoice_state": "invoiced", "invoice_error": False})

    def action_retry_auto_invoice(self):
        failed = self.filtered(lambda p: p.invoice_state == "failed")
        failed.write({"invoice_state": "to_invoice", "invoice_error": False})
        failed._run_auto_invoicing()
        return True
