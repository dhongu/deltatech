# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
import logging
from datetime import timedelta

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class QueueJob(models.Model):
    _inherit = "queue.job"

    def start_cron_trigger(self):
        domain = [("queue_job_runner", "=", True)]
        crons = self.env["ir.cron"].sudo().with_context(active_test=False).search(domain)
        for cron in crons:
            if not cron.active:
                cron.active = True

        self._cron_trigger()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "CRON Trigger",
                "message": _("The operation will be executed in the background!"),
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def process_jobs(self):
        for job in self.filtered(lambda j: j.state == "pending"):
            job._process()

    @api.model
    def _job_runner(self, commit=True):
        job = self._acquire_one_job()
        limit_jobs = self.env["ir.config_parameter"].sudo().get_param("queue_job.limit_jobs")
        if limit_jobs:
            limit_jobs = int(limit_jobs)
        else:
            limit_jobs = 100

        job_count = 0
        while job:
            job._process(commit=commit)
            job = self._acquire_one_job()
            job_count += 1
            if job_count >= limit_jobs:
                if job:
                    job._ensure_cron_trigger()
                    job._cron_trigger()
                break
        _logger.info("Job runner finished")

    @api.model
    def _cron_trigger(self, at=None):
        domain = [("queue_job_runner", "=", True)]
        crons = self.env["ir.cron"].sudo().search(domain)
        for cron in crons:
            trigger = self.env["ir.cron.trigger"].search([("cron_id", "=", cron.id)])
            if trigger:
                try:
                    trigger.unlink()
                except Exception as e:
                    _logger.error("Error deleting trigger: %s", e)
            if not at:
                at = fields.Datetime.now() + timedelta(seconds=5)
            cron._trigger(at=at)
            _logger.info(f"CRON trigger for {cron.name} at {at}")
