# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
import logging

from odoo import _, api, models

_logger = logging.getLogger(__name__)


class QueueJob(models.Model):
    _inherit = "queue.job"

    def start_cron_trigger(self):
        _logger.info("Starting CRON trigger")
        domain = [("queue_job_runner", "=", True)]
        crons = self.env["ir.cron"].sudo().with_context(active_test=False).search(domain)
        for cron in crons:
            cron.active = True
            _logger.info("Starting CRON trigger for %s", cron.name)
            cron._trigger()

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
            limit_jobs = 10

        job_count = 0
        while job:
            job._process(commit=commit)
            job = self._acquire_one_job()
            job_count += 1
            if job_count >= limit_jobs:
                if job:
                    job._ensure_cron_trigger()
                break
