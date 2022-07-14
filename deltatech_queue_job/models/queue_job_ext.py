# ©  2021 Deltatech
# See README.rst file on addons root folder for license details

import logging
import threading
import traceback
from io import StringIO

from psycopg2 import OperationalError

from odoo import SUPERUSER_ID, _, api, fields, models, registry, tools
from odoo.service.model import PG_CONCURRENCY_ERRORS_TO_RETRY
from odoo.tools.safe_eval import safe_eval

from ..exception import FailedJobError, NothingToDoJob, RetryableJobError
from ..job import ENQUEUED, PENDING, Job

PG_RETRY = 5  # seconds
_logger = logging.getLogger(__name__)


class QueueJob(models.Model):
    _inherit = "queue.job"

    def run(self):
        for record in self:
            record._change_job_state(ENQUEUED)
            record.runjob(record.uuid)

    def stop(self):
        for thread in threading.enumerate():
            _logger.info(thread.name)
            if thread.name == "background_job_%s" % self.id:
                _logger.info("It's still running")
                thread.join()
                # todo: de oprit rularea
        self.write({"state": "failed"})

    def background_run(self):
        threading_active = threading.active_count()
        _logger.info(threading_active)
        if threading_active > 15:
            return
        try:
            threaded_job = threading.Thread(target=self._do_run_background, args=(), name="background_job_%s" % self.id)
            threaded_job.start()
        except RuntimeError:
            pass

    def _do_run_background(self):
        # time.sleep(10)  # sa apuce sistemul sa salveze datele
        with api.Environment.manage():
            with self.pool.cursor() as new_cr:
                job = self.with_env(self.env(cr=new_cr))
                cron = job.env.ref("deltatech_queue_job.ir_cron_queue_job")
                new_cr.execute(
                    """SELECT *   FROM ir_cron   WHERE id=%s   FOR UPDATE NOWAIT""",
                    (cron.id,),
                    log_exceptions=False,
                )

                locked_job = new_cr.fetchone()
                if not locked_job:
                    _logger.debug("Job `%s` already executed by another process/thread. skipping it", cron.name)

                # job = self.with_env(self.env(cr=new_cr))
                # job._change_job_state(ENQUEUED)
                # job.runjob(job.uuid)
                # new_cr.commit()

    def _cron_runjob(self):
        self._run_job_in_threaded()
        # threaded_job = threading.Thread(target=self._run_job_in_threaded, args=(), name="queue_job")
        # threaded_job.start()

    def _run_job_in_threaded(self):
        new_cr = registry(self._cr.dbname).cursor()
        env = api.Environment(new_cr, SUPERUSER_ID, {})
        self = self.with_env(env(cr=new_cr))

        run = True
        _logger.info("Start CRON job")
        get_param = self.env["ir.config_parameter"].sudo().get_param
        limit = safe_eval(get_param("queue_job.select_limit", "100"))

        while run:
            records = self.search([("state", "=", ENQUEUED)], order="date_created", limit=limit)  # agatate
            limit = limit - len(records)
            if limit > 0:
                records |= self.search([("state", "=", PENDING)], order="date_created", limit=limit)

            if not records:
                run = False
            for record in records:
                if record.state == PENDING:
                    if record.eta and record.eta > fields.Datetime.now():
                        continue
                    record._change_job_state(ENQUEUED)
                    new_cr.commit()
                    # pylint: disable=E8102
                    # self.env.cr.commit()

                _logger.info("Start job: %s" % record.uuid)
                try:
                    record.runjob(record.uuid)
                    _logger.info("End job: %s" % record.uuid)
                except Exception:
                    _logger.info("End with error job : %s" % record.uuid)

        _logger.info("End CRON job")
        new_cr.close()

    def _try_perform_job(self, env, job):
        """Try to perform the job."""
        job.set_started()
        job.store()
        env.cr.commit()
        _logger.debug("%s started", job)

        job.perform()
        job.set_done()
        job.store()
        env["base"].flush()
        env.cr.commit()
        _logger.debug("%s done", job)

    def runjob(self, job_uuid):
        # http.request.session.db = db
        env = self.env(user=SUPERUSER_ID)

        def retry_postpone(job, message, seconds=None):
            job.env.clear()
            new_cr = registry(job._cr.dbname).cursor()
            env = api.Environment(new_cr, SUPERUSER_ID, {})

            job.env = env
            job.postpone(result=message, seconds=seconds)
            job.set_pending(reset_retry=False)
            job.store()
            new_cr.commit()

        # ensure the job to run is in the correct state and lock the record
        env.cr.execute("SELECT state FROM queue_job WHERE uuid=%s  FOR UPDATE", (job_uuid,))
        if not env.cr.fetchone():
            _logger.warning("was requested to run job %s, but it does not exist ", job_uuid)
            return ""

        job = Job.load(env, job_uuid)
        assert job and job.state == ENQUEUED

        try:
            try:
                self._try_perform_job(env, job)
            except OperationalError as err:
                # Automatically retry the typical transaction serialization
                # errors
                if err.pgcode not in PG_CONCURRENCY_ERRORS_TO_RETRY:
                    raise

                retry_postpone(job, tools.ustr(err.pgerror, errors="replace"), seconds=PG_RETRY)
                _logger.debug("%s OperationalError, postponed", job)

        except NothingToDoJob as err:
            if str(err):
                msg = str(err)
            else:
                msg = _("Job interrupted and set to Done: nothing to do.")
            job.set_done(msg)
            job.store()
            env.cr.commit()

        except RetryableJobError as err:
            # delay the job later, requeue
            retry_postpone(job, str(err), seconds=err.seconds)
            _logger.debug("%s postponed", job)

        except (FailedJobError, Exception):
            buff = StringIO()
            traceback.print_exc(file=buff)
            _logger.error(buff.getvalue())
            job.env.clear()
            new_cr = registry(job.env.cr.dbname).cursor()
            env = api.Environment(new_cr, SUPERUSER_ID, {})
            job.env = env
            job.set_failed(exc_info=buff.getvalue())
            job.store()
            new_cr.commit()
            raise

        return ""
