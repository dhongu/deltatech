# ©  2024 Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, models
from odoo.tools import SQL

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.model
    def _cron_clean_generated_pdfs(
        self, res_model, mimetypes, limit=100, pattern="", max_date_days=False, dry_run=False
    ):
        """
        Delete generated pdf attachments of a model, in batches, reporting the cron progress
        :param res_model: model of the documents the attachments belong to
        :param mimetypes: list of mimetypes to delete
        :param limit: limit of attachments to delete
        :param pattern: the beginning of the attachment name to delete
        :param max_date_days: relative days from which the attachments will be deleted.
        Ex. 30 = attachments will be deleted if older than today - 30 days
        :param dry_run: if set to True, just selects the attachments and does not delete anything
        :return: list of (id, file_size) of the selected attachments
        """
        if not max_date_days:
            max_date = datetime.now() - relativedelta(days=1)
        else:
            max_date = datetime.now() - relativedelta(days=max_date_days)
        if not pattern:
            pattern = "%%"
        where = SQL(
            "mimetype = ANY(%s) AND res_model = %s AND create_date <= %s AND name like %s",
            list(mimetypes),
            res_model,
            max_date,
            pattern,
        )
        self.env.cr.execute(SQL("SELECT id, file_size FROM ir_attachment WHERE %s LIMIT %s", where, limit))
        res = self.env.cr.fetchall()
        attachment_ids = [item[0] for item in res]
        sum_sizes = sum(item[1] or 0 for item in res)

        done = 0
        if not dry_run and attachment_ids:
            attachments = self.env["ir.attachment"].browse(attachment_ids)
            try:
                with self.env.cr.savepoint():
                    attachments.sudo().unlink()
                done = len(attachment_ids)
            except Exception as e:
                _logger.info(e)
        _logger.info(
            "Deleted %s attachments (%s selected), total size: %s MB",
            done,
            len(attachment_ids),
            round(sum_sizes / (1024 * 1024), 3),
        )

        # dry run or failed unlink: nothing advanced, so nothing remains for this run
        remaining = 0
        if done:
            self.env.cr.execute(SQL("SELECT count(*) FROM ir_attachment WHERE %s", where))
            remaining = self.env.cr.fetchone()[0]
        self.env["ir.cron"]._cron_report_progress(done, remaining)
        return res
