# ©  2022 Deltatech
# See README.rst file on addons root folder for license details


import logging
import os
import threading
from datetime import datetime

import psycopg2

import odoo
from odoo import api, fields, models

BASE_VERSION = odoo.modules.load_information_from_description_file("base")["version"]
_logger = logging.getLogger(__name__)


class BadVersion(Exception):
    pass


class BadModuleState(Exception):
    pass


class IrCron(models.Model):
    _inherit = "ir.cron"

    @api.model
    def create(self, values):
        values["usage"] = "ir_cron"
        if os.getenv("ODOO_NOTIFY_CRON_CHANGES"):
            self._cr.postcommit.add(self._notifydb)
        return super(IrCron, self).create(values)

    def write(self, vals):
        self._try_lock()
        if ("nextcall" in vals or vals.get("active")) and os.getenv("ODOO_NOTIFY_CRON_CHANGES"):
            self._cr.postcommit.add(self._notifydb)
        return super(IrCron, self).write(vals)

    @classmethod
    def _process_jobs(cls, db_name):
        cls._process_jobs_trigger(db_name)
        super(IrCron, cls)._process_jobs(db_name)

    @classmethod
    def _process_jobs_trigger(cls, db_name):
        """Execute every job ready to be run on this database."""
        try:
            db = odoo.sql_db.db_connect(db_name)
            threading.current_thread().dbname = db_name
            with db.cursor() as cron_cr:
                cls._check_version(cron_cr)
                jobs = cls._get_all_ready_jobs(cron_cr)
                if not jobs:
                    return
                cls._check_modules_state(cron_cr, jobs)
                job_ids = tuple(job["id"] for job in jobs)

                while True:
                    job = cls._acquire_one_job(cron_cr, job_ids)
                    if not job:
                        break
                    _logger.debug("job %s acquired", job["id"])
                    # take into account overridings of _process_job() on that database
                    registry = odoo.registry(db_name)
                    registry[cls._name]._process_job(db, cron_cr, job)
                    _logger.debug("job %s updated and released", job["id"])

        except BadVersion:
            _logger.warning("Skipping database %s as its base version is not %s.", db_name, BASE_VERSION)
        except BadModuleState:
            _logger.warning("Skipping database %s because of modules to install/upgrade/remove.", db_name)
        except psycopg2.ProgrammingError as e:
            if e.pgcode == "42P01":
                # Class 42 — Syntax Error or Access Rule Violation; 42P01: undefined_table
                # The table ir_cron does not exist; this is probably not an OpenERP database.
                _logger.warning("Tried to poll an undefined table on database %s.", db_name)
            else:
                raise
        except Exception:
            _logger.warning("Exception in cron:", exc_info=True)

    @classmethod
    def _acquire_one_job(cls, cr, job_ids):
        """Acquire one job for update from the job_ids tuple."""

        # We have to make sure ALL jobs are executed ONLY ONCE no matter
        # how many cron workers may process them. The exlusion mechanism
        # is twofold: (i) prevent parallel processing of the same job,
        # and (ii) prevent re-processing jobs that have been processed
        # already.
        #
        # (i) is implemented via `LIMIT 1 FOR UPDATE SKIP LOCKED`, each
        # worker just acquire one available job at a time and lock it so
        # the other workers don't select it too.
        # (ii) is implemented via the `WHERE` statement, when a job has
        # been processed, its nextcall is updated to a date in the
        # future and the optionnal trigger is removed.
        #
        # An `UPDATE` lock type is the strongest row lock, it conflicts
        # with ALL other lock types. Among them the `KEY SHARE` row lock
        # which is implicitely aquired by foreign keys to prevent the
        # referenced record from being removed while in use. Because we
        # never delete acquired cron jobs, foreign keys are safe to
        # concurrently reference cron jobs. Hence, the `NO KEY UPDATE`
        # row lock is used, it is a weaker lock that does conflict with
        # everything BUT `KEY SHARE`.
        #
        # Learn more: https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-ROWS

        cr.execute(
            """
                 SELECT *
                 FROM ir_cron
                 WHERE active = true
                   AND numbercall != 0
                   AND (nextcall <= (now() at time zone 'UTC')
                     OR EXISTS (
                         SELECT cron_id
                         FROM ir_cron_trigger
                         WHERE call_at <= (now() at time zone 'UTC')
                           AND cron_id = ir_cron.id
                     )
                   )
                   AND id in %s
                 ORDER BY priority
                 LIMIT 1 FOR NO KEY UPDATE SKIP LOCKED
             """,
            [job_ids],
        )
        return cr.dictfetchone()

    @classmethod
    def _process_job(cls, job_cr, job, cron_cr):

        super(IrCron, cls)._process_job(job_cr, job, cron_cr)
        cron_cr.execute(
            """
                     DELETE FROM ir_cron_trigger
                     WHERE cron_id = %s
                       AND call_at < (now() at time zone 'UTC')
                 """,
            [job["id"]],
        )

        cron_cr.commit()

    @classmethod
    def _get_all_ready_jobs(cls, cr):
        """Return a list of all jobs that are ready to be executed"""
        cr.execute(
            """
               SELECT *
               FROM ir_cron
               WHERE active = true
                 AND numbercall != 0
                 AND (  id in (
                       SELECT cron_id
                       FROM ir_cron_trigger
                       WHERE call_at <= (now() at time zone 'UTC')
                   )
                 )
               ORDER BY priority
           """
        )
        return cr.dictfetchall()

    @api.model
    def _trigger(self, at=None):
        """
        Schedule a cron job to be executed soon independently of its
        ``nextcall`` field value.
        By default the cron is scheduled to be executed in the next batch but
        the optional `at` argument may be given to delay the execution later
        with a precision down to 1 minute.
        The method may be called with a datetime or an iterable of datetime.
        The actual implementation is in :meth:`~._trigger_list`, which is the
        recommended method for overrides.
        :param Optional[Union[datetime.datetime, list[datetime.datetime]]] at:
            When to execute the cron, at one or several moments in time instead
            of as soon as possible.
        """
        if at is None:
            at_list = [fields.Datetime.now()]
        elif isinstance(at, datetime):
            at_list = [at]
        else:
            at_list = list(at)
            assert all(isinstance(at, datetime) for at in at_list)

        self._trigger_list(at_list)

    @api.model
    def _trigger_list(self, at_list):
        """
        Implementation of :meth:`~._trigger`.
        :param list[datetime.datetime] at_list:
            Execute the cron later, at precise moments in time.
        """
        if not at_list:
            return

        self.ensure_one()
        now = fields.Datetime.now()

        self.env["ir.cron.trigger"].sudo().create([{"cron_id": self.id, "call_at": at} for at in at_list])
        if _logger.isEnabledFor(logging.DEBUG):
            ats = ", ".join(map(str, at_list))
            _logger.debug("will execute '%s' at %s", self.sudo().name, ats)

        if min(at_list) <= now or os.getenv("ODOO_NOTIFY_CRON_CHANGES"):
            self._cr.postcommit.add(self._notifydb)

    def _notifydb(self):
        """Wake up the cron workers
        The ODOO_NOTIFY_CRON_CHANGES environment variable allows to force the notifydb on both
        ir_cron modification and on trigger creation (regardless of call_at)
        """
        with odoo.sql_db.db_connect("postgres").cursor() as cr:
            cr.execute("NOTIFY cron_trigger, %s", [self.env.cr.dbname])
        _logger.debug("cron workers notified")


class IrCronTrigger(models.Model):
    _name = "ir.cron.trigger"
    _description = "Triggered actions"

    cron_id = fields.Many2one("ir.cron", index=True)
    call_at = fields.Datetime()
