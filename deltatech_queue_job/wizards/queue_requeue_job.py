# Copyright 2013-2020 Camptocamp SA
# License OPL-1.0 or later (http://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class QueueRequeueJob(models.TransientModel):
    _name = "queue.requeue.job"
    _description = "Wizard to requeue a selection of jobs"

    def _default_job_ids(self):
        res = False
        context = self.env.context
        if context.get("active_model") == "queue.job" and context.get("active_ids"):
            res = context["active_ids"]
        return res

    job_ids = fields.Many2many(comodel_name="queue.job", string="Jobs", default=lambda r: r._default_job_ids())

    def requeue(self):
        jobs = self.job_ids
        jobs.requeue()
        self.env.ref("deltatech_queue_job.ir_cron_queue_job").sudo()._trigger()
        return {"type": "ir.actions.act_window_close"}
