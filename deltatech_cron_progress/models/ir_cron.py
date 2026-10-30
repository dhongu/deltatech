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

        With ``remaining > 0`` the scheduler runs the job again by itself. Outside the
        scheduler (manual run, webhook, direct call) the context has no ``cron_id`` and
        Odoo 18 runs the job only once, so the cron is triggered for the rest.
        The cron is taken from the running progress; ``self`` is used for direct calls.

        On 19.0 only the body changes: ``_commit_progress(done, remaining=remaining)``.
        """
        if not done:
            # no progress in this batch: stop the loop (mandatory in 19.0)
            remaining = 0
        self._notify_progress(done=done, remaining=remaining, deactivate=deactivate)
        if remaining and not self.env.context.get("cron_id"):
            cron = self._cron_progress_cron() or self[:1].sudo()
            if cron:
                _logger.info("Cron %r: %s processed, %s remaining, triggered again", cron.name, done, remaining)
                cron._trigger()
        return remaining

    def _cron_progress_cron(self):
        """Return the cron of the running progress (scheduler or manual run), in sudo."""
        progress_id = self.env.context.get("ir_cron_progress_id")
        if not progress_id:
            return self.sudo().browse()
        return self.env["ir.cron.progress"].sudo().browse(progress_id).cron_id
