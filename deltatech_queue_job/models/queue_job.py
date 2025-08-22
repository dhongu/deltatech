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

        cron_triggered = self._cron_trigger()
        if cron_triggered == "triggered":
            messages = _("The operation will be executed in the background!")
            message_type = "success"
        elif cron_triggered == "exists":
            messages = _("CRON Trigger already exists")
            message_type = "warning"
        else:
            messages = _("No CRON Trigger found")
            message_type = "error"

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "CRON Trigger",
                "message": messages,
                "type": message_type,
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    @api.model
    def _acquire_specific_job(self, job_id):
        """Acquire the next job to be run.

        :returns: queue.job record (locked for update)
        """
        # TODO: This method should respect channel priority and capacity,
        #       rather than just fetching them by creation date.
        self.env.flush_all()
        self.env.cr.execute(
            """
            SELECT id
            FROM queue_job
            WHERE  id = %(job_id)s
             FOR NO KEY UPDATE SKIP LOCKED
            """,
            {"job_id": job_id},
        )
        row = self.env.cr.fetchone()
        return self.browse(row and row[0])

    def process_jobs(self):
        for job in self.filtered(lambda j: j.state in ["pending", "enqueued"]):
            job._process()

    @api.model
    def _job_runner(self, commit=True):
        limit_jobs = self.env["ir.config_parameter"].sudo().get_param("queue_job.limit_jobs", "10")
        limit_jobs = int(limit_jobs)
        jobs = self.search([("state", "=", "pending")], limit=limit_jobs + 1)

        need_retrigger = False
        if len(jobs) > limit_jobs:
            at = fields.Datetime.now() + timedelta(minutes=5)
            self._cron_trigger(at)
            need_retrigger = True
        for job in jobs[:limit_jobs]:
            job = self._acquire_specific_job(job.id)
            if job and job.state == "pending":
                try:
                    job._process(commit=commit)
                except Exception as e:
                    _logger.error(f"Error processing job {job.id}: {e}")
                    continue
        if need_retrigger:
            _logger.info("Need to retrigger cron job")
            self._cron_trigger()

        _logger.info("Job runner finished")

    # @api.model
    # def _job_runner(self, commit=True):
    #     job = self._acquire_one_job()
    #     limit_jobs = self.env["ir.config_parameter"].sudo().get_param("queue_job.limit_jobs")
    #     if limit_jobs:
    #         limit_jobs = int(limit_jobs)
    #     else:
    #         limit_jobs = 100
    #
    #     job_count = 0
    #     while job:
    #         job._process(commit=commit)
    #         job = self._acquire_one_job()
    #         job_count += 1
    #         if job_count >= limit_jobs:
    #             if job:
    #                 job._ensure_cron_trigger()
    #                 job._cron_trigger()
    #             break
    #     _logger.info("Job runner finished")

    @api.model
    def _cron_trigger(self, at=None):
        domain = [("queue_job_runner", "=", True)]
        crones = self.env["ir.cron"].sudo().search(domain)
        res = "nothing"
        for cron in crones:
            domain = [("cron_id", "=", cron.id)]
            if at:
                domain.append(("call_at", "=", at))
            trigger = self.env["ir.cron.trigger"].search(domain, limit=1)
            if trigger:
                res = "exists"
                cron._trigger()
            else:
                res = "triggered"
                if not at:
                    at = fields.Datetime.now() + timedelta(seconds=5)
                cron._trigger(at=at)

                _logger.info(f"CRON trigger for {cron.name} at {at}")

        return res
