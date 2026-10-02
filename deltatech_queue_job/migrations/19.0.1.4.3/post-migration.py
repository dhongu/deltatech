# © 2026 Deltatech / Terrabit
# QUEUE-002: drop the shared placeholder API key shipped by previous versions.
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

PLACEHOLDER = "sk_live_CHANGE_ME_generate_random_key_here_123456789"


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    params = env["ir.config_parameter"].search(
        [("key", "=", "queue_job_processor.api_key"), ("value", "=", PLACEHOLDER)]
    )
    if params:
        params.unlink()
        _logger.warning(
            "deltatech_queue_job: the shared placeholder API key was removed; the queue processor "
            "API is disabled until a key is generated in Settings > Queue Job."
        )
