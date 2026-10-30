# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    create_invoice_automatically = fields.Boolean(string="Create Invoice Automatically")
    post_invoice_automatically = fields.Boolean(string="Post Invoice Automatically", default=True)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    invoice_state = fields.Selection(
        [("to_invoice", "To Invoice"), ("invoiced", "Invoiced"), ("failed", "Failed")],
        string="Invoice State",
        copy=False,
    )

    def _action_done(self):
        res = super()._action_done()

        for picking in self:
            if picking.picking_type_id.create_invoice_automatically:
                picking.invoice_state = "to_invoice"

        return res

    @api.model
    def _cron_generate_invoices(self):
        # TODO: _cron_report_progress
        pickings = self.search([("invoice_state", "=", "to_invoice")], limit=100)
        for picking in pickings:
            if picking.invoice_state != "to_invoice":
                continue
            try:
                # each picking in its own savepoint: an SQL error must not abort the whole batch
                with self.env.cr.savepoint():
                    picking._generate_invoice_automatically()
            except Exception as e:
                _logger.exception("Error in automatic invoicing for picking %s", picking.name)
                # written outside the savepoint, so it survives the rollback
                picking.invoice_state = "failed"
                picking.message_post(body=_("Automatic invoicing failed: %s", e))

    def _generate_invoice_automatically(self):
        self.ensure_one()
        sale_orders = self.sale_id
        if not sale_orders:
            return
        sale_orders.order_line._compute_qty_delivered()
        invoices = sale_orders._create_invoices(final=True)
        if self.picking_type_id.post_invoice_automatically:
            invoices.filtered(lambda i: i.state == "draft").action_post()

        # mark all pickings of the same sale as invoiced
        all_pickings = self.search([("sale_id", "in", sale_orders.ids), ("invoice_state", "=", "to_invoice")])
        all_pickings.write({"invoice_state": "invoiced"})
