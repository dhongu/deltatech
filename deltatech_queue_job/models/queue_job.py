# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class QueueJob(models.Model):
    _inherit = "queue.job"

    def start_cron_trigger(self):
        self._cron_trigger()

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
            _logger.info("Processing job %s", job.name)
            job._process(commit=commit)
            job = self._acquire_one_job()
            job_count += 1
            if job_count >= limit_jobs:
                if job:
                    job._ensure_cron_trigger()
                break
