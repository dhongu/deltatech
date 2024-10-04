# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models


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
            job._process(commit=commit)
            job = self._acquire_one_job()
            job_count += 1
            if job_count >= limit_jobs:
                if job:
                    self._cron_trigger()
                break
