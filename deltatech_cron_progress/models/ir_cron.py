# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class IrCron(models.Model):
    _inherit = "ir.cron"

    def _cron_report_progress(self, done: int, remaining: int, deactivate: bool = False) -> int:
        """Report the progress of a batch run by a cron job.

        Call it once, at the end of the batch, in the method run by the cron.

        :param done: number of records processed in this batch (not a running total)
        :param remaining: number of records still to process
        :param deactivate: deactivate the cron once everything is processed (one-shot crons)
        :return: the remaining value actually reported

        In a cron run (scheduler or "Run manually") the progress goes to ``_commit_progress``,
        which **commits** the transaction; with ``remaining > 0`` the job runs again by itself.
        Outside a cron run (direct call from code) nothing is committed and the cron the
        helper is called on is triggered for the rest.
        """
        if not done:
            # no progress in this batch: stop the loop, otherwise 19.0 retries it right away
            remaining = 0
        if self.env.context.get("ir_cron_progress_id"):
            self._commit_progress(done, remaining=remaining, deactivate=deactivate)
        elif remaining:
            cron = self[:1].sudo()
            if cron:
                _logger.info("Cron %r: %s processed, %s remaining, triggered again", cron.name, done, remaining)
                cron._trigger()
        return remaining
