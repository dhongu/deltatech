# ©  2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import logging
import secrets
import time

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

# Placeholder shipped by versions <= 19.0.1.4.2; identical on every installation,
# so it must never authenticate (QUEUE-002).
PLACEHOLDER_API_KEYS = {"sk_live_CHANGE_ME_generate_random_key_here_123456789"}


def _check_api_key(api_key):
    """True only for the configured key; an empty or shipped placeholder key disables the API."""
    expected_key = request.env["ir.config_parameter"].sudo().get_param("queue_job_processor.api_key")
    if not expected_key or expected_key in PLACEHOLDER_API_KEYS:
        _logger.warning("Queue processor API disabled: generate an API key in Settings > Queue Job.")
        return False
    if not api_key or not isinstance(api_key, str):
        return False
    return secrets.compare_digest(api_key.encode(), expected_key.encode())


class QueueJobProcessorController(http.Controller):
    @http.route("/run_jobs", type="http", auth="user", methods=["POST"], csrf=False)
    def run_jobs(self, **kwargs):
        request.env["queue.job"]._run_pending_jobs()
        return "Jobs executed"

    @http.route("/api/v1/queue/process", type="jsonrpc", auth="public", methods=["POST"], csrf=False)
    def process_queue_jobs(self, api_key=None, batch_size=None, max_seconds=None, **kw):
        """
        Process pending queue jobs

        Called by external cron service (cron-job.org)

        Parameters:
        -----------
        api_key : str
            API key for authentication
        batch_size : int
            Maximum number of jobs to process (default: from config or 20)
        max_seconds : int
            Maximum processing time in seconds (default: from config or 50)

        Returns:
        --------
        dict : Processing results and statistics
        """
        # Verify API key
        ConfigParam = request.env["ir.config_parameter"].sudo()
        if not _check_api_key(api_key):
            _logger.warning("⛔ Unauthorized queue processing attempt")
            return {
                "jsonrpc": "2.0",
                "id": None,
                "result": {"status": "error", "message": "Unauthorized - Invalid API key", "code": 401},
            }

        # Load default values from config if not provided
        if batch_size is None:
            batch_size = int(ConfigParam.get_param("queue_job_processor.batch_size", 20))
        if max_seconds is None:
            max_seconds = int(ConfigParam.get_param("queue_job_processor.max_seconds", 50))

        try:
            QueueJob = request.env["queue.job"].sudo()
            # Find any pending jobs (even without locking, as we just want to know if there's work)
            pending_count = QueueJob.search_count([("state", "=", "pending")])

            if pending_count == 0:
                return {
                    "jsonrpc": "2.0",
                    "id": None,
                    "result": {
                        "status": "success",
                        "message": "No pending jobs in queue",
                        "processed": 0,
                        "pending_count": 0,
                    },
                }

            # Execute jobs via the dedicated API runner
            api_results = QueueJob._api_job_runner(batch_size=batch_size, max_seconds=max_seconds)

            result = {
                "status": "success",
                "processed": api_results["processed"],
                "done": api_results["done"],
                "failed": api_results["failed"],
                "postponed": api_results["postponed"],
                "pending_count": api_results["pending_remaining"],
                "time_elapsed": api_results["time_elapsed"],
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }

            _logger.info(
                "✅ API processing finished - Processed: %d, Done: %d, Failed: %d, Postponed: %d, Time: %.2fs",
                api_results["processed"],
                api_results["done"],
                api_results["failed"],
                api_results["postponed"],
                api_results["time_elapsed"],
            )

            return {"jsonrpc": "2.0", "id": None, "result": result}

        except Exception as e:
            _logger.error("💥 Fatal error in queue processor API: %s", str(e), exc_info=True)
            return {"jsonrpc": "2.0", "id": None, "result": {"status": "error", "message": str(e), "code": 500}}

    @http.route("/api/v1/queue/stats", type="jsonrpc", auth="public", methods=["GET", "POST"], csrf=False)
    def get_queue_stats(self, api_key=None, **kw):
        """
        Get queue statistics

        Returns current queue status without processing
        """
        if not _check_api_key(api_key):
            return {"jsonrpc": "2.0", "result": {"status": "error", "message": "Unauthorized"}}

        try:
            QueueJob = request.env["queue.job"].sudo()

            stats = {
                "pending": QueueJob.search_count([("state", "=", "pending")]),
                "started": QueueJob.search_count([("state", "=", "started")]),
                "done": QueueJob.search_count([("state", "=", "done")]),
                "failed": QueueJob.search_count([("state", "=", "failed")]),
                "total": QueueJob.search_count([]),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }

            return {"jsonrpc": "2.0", "result": {"status": "success", "stats": stats}}

        except Exception as e:
            _logger.error("Error getting queue stats: %s", str(e))
            return {"jsonrpc": "2.0", "result": {"status": "error", "message": str(e)}}
