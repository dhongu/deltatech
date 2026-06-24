# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
import logging
import threading
import time
from datetime import timedelta

from odoo import _, api, fields, models, modules

_logger = logging.getLogger(__name__)


class QueueJob(models.Model):
    _inherit = "queue.job"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._remove_failed_duplicates()
        return records

    def _remove_failed_duplicates(self):
        """Cancel older jobs left in 'failed' state that share the same
        identity_key as a freshly created job.

        The standard deduplication (job_record_with_same_identity_key) only
        considers active states (pending/enqueued/wait_dependencies), so a
        failed job never blocks a new enqueue and dead duplicates pile up.
        When a new job with the same identity_key is created we move the
        previous failed ones to 'cancelled': the record (and its traceback) is
        kept for diagnostics and the standard autovacuum cron will remove it
        later based on the channel removal_interval.
        """
        keys = {record.identity_key for record in self if record.identity_key}
        if not keys:
            return
        old_failed = self.sudo().search(
            [
                ("identity_key", "in", list(keys)),
                ("state", "=", "failed"),
                ("id", "not in", self.ids),
            ]
        )
        if old_failed:
            _logger.info(
                "Cancelling %d failed job(s) superseded by a new job with the same identity_key",
                len(old_failed),
            )
            old_failed._change_job_state(
                "cancelled",
                result=_("Superseded by a new job with the same identity_key"),
            )

    @api.model
    def _api_job_runner(self, batch_size=20, max_seconds=50):
        """Runner dedicated to External API calls (e.g. cron-job.org)"""
        start_time = time.time()
        processed = 0
        failed = 0

        _logger.info("🚀 Starting queue processing via API - Batch size: %d", batch_size)

        # We acquire one job at a time to respect concurrency and locking
        job = self._acquire_one_job()
        while job and processed < batch_size:
            # Check time budget
            elapsed = time.time() - start_time
            if elapsed > max_seconds:
                _logger.warning("⏱️ Time budget exceeded (%.1fs > %ds), stopping.", elapsed, max_seconds)
                break

            try:
                # Process the job (includes its own internal commit/rollback)
                job._process(commit=True)
                processed += 1
            except Exception as e:
                failed += 1
                _logger.error("❌ Job %s failed in API runner: %s", job.id, str(e))

            job = self._acquire_one_job()

        return {
            "processed": processed,
            "failed": failed,
            "time_elapsed": round(time.time() - start_time, 2),
            "pending_remaining": self.search_count([("state", "=", "pending")]),
        }

    @api.model
    def _process_api_in_thread(self, dbname, uid, context):
        """Method to be executed in a separate thread"""
        with modules.registry.Registry(dbname).cursor() as cr:
            env = api.Environment(cr, uid, context)
            try:
                env["queue.job"]._api_job_runner()
            except Exception as e:
                _logger.error("Error in threaded API runner: %s", str(e))

    def action_process_api_thread(self):
        """Action to trigger API processing in a separate thread"""
        dbname = self.env.cr.dbname
        uid = self.env.uid
        context = self.env.context

        thread = threading.Thread(target=self._process_api_in_thread, args=(dbname, uid, context), daemon=True)
        thread.start()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Thread Processing"),
                "message": _("The API processing has been triggered in a separate thread!"),
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

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
        """Action for manual job processing from UI in background"""
        # If specific jobs were selected, we could mark them or just trigger the cron.
        # But for background processing, we just trigger the cron runner.
        self._ensure_cron_trigger()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Job Processing Started"),
                "message": _("The processing of jobs has been triggered in the background."),
                "type": "success",
                "sticky": False,
            },
        }

    @api.model
    def _job_runner(self, commit=True):
        """Short-lived job runner with limit and re-trigger"""
        batch_size = self.env["ir.config_parameter"].sudo().get_param("queue_job_processor.batch_size", "20")
        batch_size = int(batch_size)
        max_seconds = self.env["ir.config_parameter"].sudo().get_param("queue_job_processor.max_seconds", "50")
        max_seconds = int(max_seconds)

        start_time = time.time()

        # We search with limit+1 to see if we need to re-trigger
        now = fields.Datetime.now()
        domain = [("state", "=", "pending"), "|", ("eta", "=", False), ("eta", "<=", now)]
        jobs = self.search(domain, order="priority, date_created", limit=batch_size + 1)

        need_retrigger = False
        if len(jobs) > batch_size:
            need_retrigger = True

        processed_count = 0
        for job in jobs[:batch_size]:
            # Check time budget
            elapsed = time.time() - start_time
            if elapsed > max_seconds:
                _logger.warning("⏱️ Time budget exceeded (%.1fs > %ds) in cron runner, stopping.", elapsed, max_seconds)
                need_retrigger = True
                break

            # Try to acquire the job exclusively
            job = self._acquire_specific_job(job.id)
            if job and job.state == "pending":
                try:
                    job._process(commit=commit)
                    processed_count += 1
                except Exception as e:
                    _logger.error("Error processing job %s: %s", job.id, e)
                    continue

        if need_retrigger:
            _logger.info("Need to retrigger cron job")
            self._cron_trigger()

        _logger.info("Job runner finished. Processed %d jobs in %.2fs.", processed_count, time.time() - start_time)

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
