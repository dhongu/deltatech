# ©  2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import secrets

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    queue_job_processor_api_key = fields.Char(
        string="API Key",
        config_parameter="queue_job_processor.api_key",
        help="API Key for external queue processor (cron-job.org)",
    )
    queue_job_processor_batch_size = fields.Integer(
        string="Batch Size",
        config_parameter="queue_job_processor.batch_size",
        default=20,
        help="Maximum number of jobs to process per execution",
    )
    queue_job_processor_max_seconds = fields.Integer(
        string="Max Seconds",
        config_parameter="queue_job_processor.max_seconds",
        default=50,
        help="Maximum execution time in seconds",
    )

    def action_generate_queue_job_processor_api_key(self):
        self.queue_job_processor_api_key = secrets.token_urlsafe(32)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "API Key Generated",
                "message": "A new API key has been generated. Remember to save settings.",
                "type": "success",
                "sticky": False,
            },
        }
