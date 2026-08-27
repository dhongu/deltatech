# ©  2024 Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, models
from odoo.tools import str2bool

from .cleanup_summary import autovacuum_run, log_prefix, rows_summary

PREFIX = "deltatech_actions."

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.autovacuum
    def _gc_generated_pdfs(self):
        """Run the sale order PDF cleanup from the autovacuum job -- see autovacuum_run()."""
        return autovacuum_run(self, "cron_clean_generated_pdfs_from_settings", PREFIX + "sale_pdf_limit")

    @api.model
    def cron_clean_generated_pdfs_from_settings(self):
        """Entry point used by the cron: reads its parameters from Settings
        (General Settings > Database Cleanup) instead of hardcoded values."""
        icp = self.env["ir.config_parameter"].sudo()
        dry_run = str2bool(icp.get_param("deltatech_actions.sale_pdf_dry_run", "True"))
        rows = self.cron_clean_generated_pdfs(
            limit=int(icp.get_param("deltatech_actions.sale_pdf_limit", 5000)),
            pattern=icp.get_param("deltatech_actions.sale_pdf_pattern", "") or "",
            max_date_days=int(icp.get_param("deltatech_actions.sale_pdf_max_date_days", 90)),
            dry_run=dry_run,
        )
        return rows_summary(rows, dry_run)

    def force_cancel_order_and_moves(self):
        """
        Cancel sale order, attached pickings, stock moves and stock move lines.
        :return:
        """
        stock_move_lines_to_cancel = self.env["stock.move.line"]
        stock_moves_to_cancel = self.env["stock.move"]
        pickings_to_cancel = self.env["stock.picking"]
        account_moves_to_cancel = self.env["account.move"]
        # sale_orders_to_cancel = []
        for order in self:
            if order.state == "sale" and order.picking_ids:
                for picking in order.picking_ids:
                    stock_moves_to_cancel |= picking.move_ids
                    account_moves_to_cancel |= picking.move_ids.account_move_ids
                    stock_move_lines_to_cancel |= picking.move_ids.move_line_ids
                    pickings_to_cancel |= picking

        stock_move_lines_to_cancel.write({"state": "cancel"})
        account_moves_to_cancel.write({"state": "cancel"})
        stock_moves_to_cancel.write({"state": "cancel"})
        pickings_to_cancel.write({"state": "cancel"})
        self.write({"state": "cancel"})

    @api.model
    def cron_clean_generated_pdfs(self, limit=100, pattern="", max_date_days=False, dry_run=False):
        """
        Delete generated pdf from sale orders
        :param limit: limit of attachments to delete
        :param pattern: the beginning of the attachment name to delete
        :param max_date_days: relative days from which the attachments will be deleted.
        Ex. 30 = attachments will be deleted if older than today - 30 days
        :param dry_run: if set to True, just selects the attachments and does not delete anything
        :return: None
        """
        if not max_date_days:
            max_date = datetime.now() - relativedelta(days=1)
        else:
            max_date = datetime.now() - relativedelta(days=max_date_days)
        if not pattern:
            pattern = "%%"
        query = """SELECT id,file_size FROM ir_attachment
                        WHERE mimetype='application/pdf' AND res_model='sale.order'
                        AND create_date <= %(create_date)s AND name like %(pattern)s
                        limit %(limit)s;
                        """
        params = {"limit": limit, "create_date": max_date, "pattern": pattern}
        self.env.cr.execute(query, params=params)
        res = self.env.cr.fetchall()
        attachment_ids = [item[0] for item in res]
        sizes = [item[1] for item in res]
        sum_sizes = 0
        for size in sizes:
            sum_sizes += size
        if not dry_run:
            attachments = self.env["ir.attachment"].browse(attachment_ids)
            try:
                attachments.sudo().unlink()
            except Exception as e:
                _logger.info(e)
        _logger.info(
            f"{log_prefix(dry_run)} {len(attachment_ids)} attachments, "
            f"total size: {round(sum_sizes / (1024 * 1024), 3)} MB"
        )
        return res
