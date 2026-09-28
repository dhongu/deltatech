# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
import logging
from datetime import timedelta

from odoo import fields

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Schedule the first computation instead of running it here.

    A full recompute inside the install request runs under the web worker's
    time limit. On a large database the worker is killed and the install is
    rolled back (seen at MD Trade on a test instance). The cron runs in its own
    worker, one minute after the install.
    """
    cron = env.ref("deltatech_customer_segment.ir_cron_customer_segment_recompute", raise_if_not_found=False)
    if not cron:
        _logger.warning("deltatech_customer_segment: recompute cron not found")
        return
    cron.sudo().nextcall = fields.Datetime.now() + timedelta(minutes=1)
