# ©  2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import http
from odoo.http import request


class QueueJobManualTrigger(http.Controller):
    @http.route("/run_jobs", type="http", auth="user", methods=["POST"], csrf=False)
    def run_jobs(self, **kwargs):
        request.env["queue.job"]._run_pending_jobs()
        return "Jobs executed"
