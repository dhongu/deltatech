# ©  2024 Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, models
from odoo.tools import str2bool

from .cleanup_summary import log_prefix, rows_summary

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def cron_clean_generated_pdfs_from_settings(self):
        """Entry point used by the cron: reads its parameters from Settings
        (General Settings > Database Cleanup) instead of hardcoded values."""
        icp = self.env["ir.config_parameter"].sudo()
        states = []
        if str2bool(icp.get_param("deltatech_actions.picking_pdf_only_done", "True")):
            states.append("done")
        if str2bool(icp.get_param("deltatech_actions.picking_pdf_only_cancel", "True")):
            states.append("cancel")
        dry_run = str2bool(icp.get_param("deltatech_actions.picking_pdf_dry_run", "True"))
        rows = self.cron_clean_generated_pdfs(
            limit=int(icp.get_param("deltatech_actions.picking_pdf_limit", 5000)),
            pattern=icp.get_param("deltatech_actions.picking_pdf_pattern", "") or "",
            max_date_days=int(icp.get_param("deltatech_actions.picking_pdf_max_date_days", 180)),
            dry_run=dry_run,
            states=states or None,
        )
        return rows_summary(rows, dry_run)

    @api.model
    def cron_clean_generated_pdfs(self, limit=100, pattern="", max_date_days=False, dry_run=False, states=None):
        """
        Delete generated pdf/label attachments from stock pickings (mainly
        the carrier AWB label stored in the ``label_attachment`` field --
        measured on a real deployment, that field alone accounted for
        ~36 GB across ~150k pickings, by far the largest single filestore
        consumer).
        :param limit: limit of attachments to delete
        :param pattern: the beginning of the attachment name to delete. Leave empty:
        real label filenames vary a lot by carrier -- some are the carrier's own
        report name (e.g. "LabelGLS-...pdf"), others are just the raw tracking
        number, or the field's technical name ("label_attachment") when a carrier
        integration does not set one. A narrow pattern can silently match nothing.
        :param max_date_days: relative days from which the attachments will be deleted.
        Ex. 30 = attachments will be deleted if older than today - 30 days
        :param dry_run: if set to True, just selects the attachments and does not delete anything
        :param states: optional list of stock.picking states to restrict to, e.g.
        ["done", "cancel"] -- recommended, so only finished/cancelled deliveries are
        touched, never one still in progress. Not applied when left empty, for
        backwards compatibility.
        :return: None
        """
        if not max_date_days:
            max_date = datetime.now() - relativedelta(days=1)
        else:
            max_date = datetime.now() - relativedelta(days=max_date_days)
        if not pattern:
            pattern = "%%"
        params = {"limit": limit, "create_date": max_date, "pattern": pattern}
        states_clause = ""
        if states:
            states_clause = "AND sp.state IN %(states)s"
            params["states"] = tuple(states)
        query = f"""SELECT att.id, att.file_size FROM ir_attachment att
                            JOIN stock_picking sp ON sp.id = att.res_id
                            WHERE att.res_model = 'stock.picking'
                            AND (att.mimetype = 'application/pdf' OR att.mimetype = 'application/octet-stream')
                            AND att.create_date <= %(create_date)s AND att.name like %(pattern)s
                            {states_clause}
                            limit %(limit)s;
                            """
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
