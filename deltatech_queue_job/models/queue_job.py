# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
import logging
from datetime import timedelta

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class QueueJob(models.Model):
    _inherit = "queue.job"

    @api.model
    def _run_pending_jobs(self, limit=10):
        limit_jobs = self.env["ir.config_parameter"].sudo().get_param("queue_job.limit_jobs", limit)
        limit_jobs = int(limit_jobs)
        jobs = self.search([("state", "=", "pending")], limit=limit_jobs)
        for job in jobs:
            try:
                job.perform()
            except Exception as e:
                job.set_failed(e)

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
        self.env.flush_all()
        self.env.cr.execute(
            """
            SELECT id
            FROM queue_job
            WHERE id = %(job_id)s
            FOR NO KEY UPDATE SKIP LOCKED
            """,
            {"job_id": job_id},
        )
        row = self.env.cr.fetchone()
        return self.browse(row and row[0])

    def process_jobs(self):
        for job in self.filtered(lambda j: j.state == "pending"):
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

    @api.model
    def _cron_trigger(self, at=None):
        domain = [("queue_job_runner", "=", True)]
        crones = self.env["ir.cron"].sudo().search(domain)
        res = "nothing"

        for cron in crones:
            trigger_domain = [("cron_id", "=", cron.id)]
            if at:
                trigger_domain.append(("call_at", "=", at))
            trigger = self.env["ir.cron.trigger"].search(trigger_domain, limit=1)

            if trigger and trigger.call_at >= fields.Datetime.now():
                # triggerul exista si e in viitor - valid
                res = "exists"
            else:
                # nu exista SAU e in trecut - retriggeram
                res = "triggered"
                # calculam at_trigger local, fara sa modificam parametrul `at`
                at_trigger = at or fields.Datetime.now() + timedelta(seconds=5)
                cron._trigger(at=at_trigger)
                _logger.info(f"CRON trigger scheduled for {cron.name} at {at_trigger}")

        return res
