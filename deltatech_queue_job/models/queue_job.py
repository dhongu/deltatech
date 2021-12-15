# Copyright 2013-2020 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

import logging
import threading
import traceback
from datetime import datetime, timedelta
from io import StringIO

from psycopg2 import OperationalError

from odoo import SUPERUSER_ID, _, api, exceptions, fields, models, tools
from odoo.osv import expression
from odoo.service.model import PG_CONCURRENCY_ERRORS_TO_RETRY

from ..exception import FailedJobError, NothingToDoJob, RetryableJobError
from ..fields import JobSerialized
from ..job import DONE, ENQUEUED, PENDING, STATES, Job

PG_RETRY = 5  # seconds
_logger = logging.getLogger(__name__)


class QueueJob(models.Model):
    """Model storing the jobs to be executed."""

    _name = "queue.job"
    _description = "Queue Job"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _log_access = False

    _order = "date_created DESC, date_done DESC"

    _removal_interval = 30  # days
    _default_related_action = "related_action_open_record"

    # This must be passed in a context key "_job_edit_sentinel" to write on
    # protected fields. It protects against crafting "queue.job" records from
    # RPC (e.g. on internal methods). When ``with_delay`` is used, the sentinel
    # is set.
    EDIT_SENTINEL = object()
    _protected_fields = (
        "uuid",
        "name",
        "date_created",
        "model_name",
        "method_name",
        "records",
        "args",
        "kwargs",
    )

    uuid = fields.Char(string="UUID", readonly=True, index=True, required=True)
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User ID",
        compute="_compute_user_id",
        inverse="_inverse_user_id",
        store=True,
    )
    company_id = fields.Many2one(comodel_name="res.company", string="Company", index=True)
    name = fields.Char(string="Description", readonly=True)

    model_name = fields.Char(string="Model", compute="_compute_model_name", store=True, readonly=True)
    method_name = fields.Char(readonly=True)
    # record_ids field is only for backward compatibility (e.g. used in related
    # actions), can be removed (replaced by "records") in 14.0
    record_ids = JobSerialized(compute="_compute_record_ids", base_type=list)
    records = JobSerialized(
        string="Record(s)",
        readonly=True,
        base_type=models.BaseModel,
    )
    args = JobSerialized(readonly=True, base_type=tuple)
    kwargs = JobSerialized(readonly=True, base_type=dict)
    func_string = fields.Char(string="Task", compute="_compute_func_string", readonly=True, store=True)

    state = fields.Selection(STATES, readonly=True, required=True, index=True)
    priority = fields.Integer()
    exc_info = fields.Text(string="Exception Info", readonly=True)
    result = fields.Text(readonly=True)

    date_created = fields.Datetime(string="Created Date", readonly=True)
    date_started = fields.Datetime(string="Start Date", readonly=True)
    date_enqueued = fields.Datetime(string="Enqueue Time", readonly=True)
    date_done = fields.Datetime(readonly=True)

    eta = fields.Datetime(string="Execute only after")
    retry = fields.Integer(string="Current try")
    max_retries = fields.Integer(
        string="Max. retries",
        help="The job will fail if the number of tries reach the " "max. retries.\n" "Retries are infinite when empty.",
    )
    # channel_method_name = fields.Char(
    #     readonly=True, compute="_compute_job_function", store=True
    # )
    # job_function_id = fields.Many2one(
    #     comodel_name="queue.job.function",
    #     compute="_compute_job_function",
    #     string="Job Function",
    #     readonly=True,
    #     store=True,
    # )
    #
    # override_channel = fields.Char()
    # channel = fields.Char(
    #     compute="_compute_channel", inverse="_inverse_channel", store=True, index=True
    # )

    identity_key = fields.Char()
    worker_pid = fields.Integer()

    def init(self):
        self._cr.execute(
            "SELECT indexname FROM pg_indexes WHERE indexname = %s ",
            ("queue_job_identity_key_state_partial_index",),
        )
        if not self._cr.fetchone():
            self._cr.execute(
                "CREATE INDEX queue_job_identity_key_state_partial_index "
                "ON queue_job (identity_key) WHERE state in ('pending', "
                "'enqueued') AND identity_key IS NOT NULL;"
            )

    @api.depends("records")
    def _compute_user_id(self):
        for record in self:
            record.user_id = record.records.env.uid

    def _inverse_user_id(self):
        for record in self.with_context(_job_edit_sentinel=self.EDIT_SENTINEL):
            record.records = record.records.with_user(record.user_id.id)

    @api.depends("records")
    def _compute_model_name(self):
        for record in self:
            record.model_name = record.records._name

    @api.depends("records")
    def _compute_record_ids(self):
        for record in self:
            record.record_ids = record.records.ids

    #
    # def _inverse_channel(self):
    #     for record in self:
    #         record.override_channel = record.channel

    # @api.depends("job_function_id.channel_id")
    # def _compute_channel(self):
    #     for record in self:
    #         channel = (
    #             record.override_channel or record.job_function_id.channel or "root"
    #         )
    #         if record.channel != channel:
    #             record.channel = channel
    #
    # @api.depends("model_name", "method_name", "job_function_id.channel_id")
    # def _compute_job_function(self):
    #     for record in self:
    #         func_model = self.env["queue.job.function"]
    #         channel_method_name = func_model.job_function_name(
    #             record.model_name, record.method_name
    #         )
    #         function = func_model.search([("name", "=", channel_method_name)], limit=1)
    #         record.channel_method_name = channel_method_name
    #         record.job_function_id = function

    @api.depends("model_name", "method_name", "records", "args", "kwargs")
    def _compute_func_string(self):
        for record in self:
            model = repr(record.records)
            args = [repr(arg) for arg in record.args]
            kwargs = ["{}={!r}".format(key, val) for key, val in record.kwargs.items()]
            all_args = ", ".join(args + kwargs)
            record.func_string = "{}.{}({})".format(model, record.method_name, all_args)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get("_job_edit_sentinel") is not self.EDIT_SENTINEL:
            # Prevent to create a queue.job record "raw" from RPC.
            # ``with_delay()`` must be used.
            raise exceptions.AccessError(_("Queue jobs must created by calling 'with_delay()'."))
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get("_job_edit_sentinel") is not self.EDIT_SENTINEL:
            write_on_protected_fields = [fieldname for fieldname in vals if fieldname in self._protected_fields]
            if write_on_protected_fields:
                raise exceptions.AccessError(_("Not allowed to change field(s): {}").format(write_on_protected_fields))

        if vals.get("state") == "failed":
            self._message_post_on_failure()

        return super().write(vals)

    def open_related_action(self):
        """Open the related action associated to the job"""
        self.ensure_one()
        job = Job.load(self.env, self.uuid)
        action = job.related_action()
        if action is None:
            raise exceptions.UserError(_("No action available for this job"))
        return action

    def _change_job_state(self, state, result=None):
        """Change the state of the `Job` object

        Changing the state of the Job will automatically change some fields
        (date, result, ...).
        """
        for record in self:
            job_ = Job.load(record.env, record.uuid)
            if state == DONE:
                job_.set_done(result=result)
            elif state == PENDING:
                job_.set_pending(result=result)
            elif state == ENQUEUED:
                job_.set_enqueued()
            else:
                raise ValueError("State not supported: %s" % state)
            job_.store()

    def button_done(self):
        result = _("Manually set to done by %s") % self.env.user.name
        self._change_job_state(DONE, result=result)
        return True

    def requeue(self):
        self._change_job_state(PENDING)
        return True

    def _message_post_on_failure(self):
        # subscribe the users now to avoid to subscribe them
        # at every job creation
        domain = self._subscribe_users_domain()
        users = self.env["res.users"].search(domain)
        self.message_subscribe(partner_ids=users.mapped("partner_id").ids)
        for record in self:
            msg = record._message_failed_job()
            if msg:
                record.message_post(body=msg, subtype_xmlid="deltatech_queue_job.mt_job_failed")

    def _subscribe_users_domain(self):
        """Subscribe all users having the 'Queue Job Manager' group"""
        group = self.env.ref("deltatech_queue_job.group_queue_job_manager")
        if not group:
            return None
        companies = self.mapped("company_id")
        domain = [("groups_id", "=", group.id)]
        if companies:
            domain.append(("company_id", "in", companies.ids))
        return domain

    def _message_failed_job(self):
        """Return a message which will be posted on the job when it is failed.

        It can be inherited to allow more precise messages based on the
        exception informations.

        If nothing is returned, no message will be posted.
        """
        self.ensure_one()
        return _(
            "Something bad happened during the execution of the job. "
            "More details in the 'Exception Information' section."
        )

    def _needaction_domain_get(self):
        """Returns the domain to filter records that require an action

        :return: domain or False is no action
        """
        return [("state", "=", "failed")]

    def autovacuum(self):
        deadline = datetime.now() - timedelta(days=int(2))
        while True:
            jobs = self.search([("date_done", "<=", deadline)], limit=1000)
            if jobs:
                jobs.unlink()
            else:
                break
        return True

    def requeue_stuck_jobs(self, enqueued_delta=5, started_delta=0):
        """Fix jobs that are in a bad states

        :param in_queue_delta: lookup time in minutes for jobs
                                that are in enqueued state

        :param started_delta: lookup time in minutes for jobs
                                that are in enqueued state,
                                0 means that it is not checked
        """
        self._get_stuck_jobs_to_requeue(enqueued_delta=enqueued_delta, started_delta=started_delta).requeue()
        return True

    def _get_stuck_jobs_domain(self, queue_dl, started_dl):
        domain = []
        now = fields.datetime.now()
        if queue_dl:
            queue_dl = now - timedelta(minutes=queue_dl)
            domain.append(
                [
                    "&",
                    ("date_enqueued", "<=", fields.Datetime.to_string(queue_dl)),
                    ("state", "=", "enqueued"),
                ]
            )
        if started_dl:
            started_dl = now - timedelta(minutes=started_dl)
            domain.append(
                [
                    "&",
                    ("date_started", "<=", fields.Datetime.to_string(started_dl)),
                    ("state", "=", "started"),
                ]
            )
        if not domain:
            raise exceptions.ValidationError(_("If both parameters are 0, ALL jobs will be requeued!"))
        return expression.OR(domain)

    def _get_stuck_jobs_to_requeue(self, enqueued_delta, started_delta):
        job_model = self.env["queue.job"]
        stuck_jobs = job_model.search(self._get_stuck_jobs_domain(enqueued_delta, started_delta))
        return stuck_jobs

    def related_action_open_record(self):
        """Open a form view with the record(s) of the job.

        For instance, for a job on a ``product.product``, it will open a
        ``product.product`` form view with the product record(s) concerned by
        the job. If the job concerns more than one record, it opens them in a
        list.

        This is the default related action.

        """
        self.ensure_one()
        records = self.records.exists()
        if not records:
            return None
        action = {
            "name": _("Related Record"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": records._name,
        }
        if len(records) == 1:
            action["res_id"] = records.id
        else:
            action.update(
                {
                    "name": _("Related Records"),
                    "view_mode": "tree,form",
                    "domain": [("id", "in", records.ids)],
                }
            )
        return action

    def _test_job(self):
        _logger.info("Running test job.")

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
        run = True
        _logger.info("Start CRON job")
        while run:
            records = self.search([("state", "=", ENQUEUED)], order="date_created", limit=5)  # agatate
            records |= self.search([("state", "=", PENDING)], order="date_created", limit=5)

            if not records:
                run = False
            for record in records:
                if record.state == PENDING:
                    if record.eta and record.eta > fields.Datetime.now():
                        continue
                    record._change_job_state(ENQUEUED)
                    # pylint: disable=E8102
                    # self.env.cr.commit()

                _logger.info("Start job: %s" % record.uuid)
                try:
                    record.runjob(record.uuid)
                    _logger.info("End job: %s" % record.uuid)
                except Exception:
                    _logger.info("End with error job : %s" % record.uuid)

        _logger.info("End CRON job")

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
            with api.Environment.manage():
                with self.pool.cursor() as new_cr:
                    job.env = job.env(cr=new_cr)
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
            with api.Environment.manage():
                with self.pool.cursor() as new_cr:
                    job.env = job.env(cr=new_cr)
                    job.set_failed(exc_info=buff.getvalue())
                    job.store()
                    new_cr.commit()
            raise

        return ""
