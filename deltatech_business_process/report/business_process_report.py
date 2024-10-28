# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class BusinessProcessReport(models.Model):
    _name = "business.process.report"
    _description = "Business process report"
    _auto = False
    _order = "project_id, process_id, sequence"

    project_id = fields.Many2one(string="Project", comodel_name="business.project", required=True)
    process_id = fields.Many2one("business.process", string="Business process", readonly=True)
    step_id = fields.Many2one(string="Step", comodel_name="business.process.step", readonly=True)
    sequence = fields.Integer(string="Sequence", readonly=True)

    area_id = fields.Many2one(string="Area", comodel_name="business.area", readonly=True)
    process_group_id = fields.Many2one(string="Process Group", comodel_name="business.process.group", readonly=True)

    responsible_id = fields.Many2one(string="Responsible", comodel_name="res.partner", readonly=True)

    customer_id = fields.Many2one(string="Customer Responsible", comodel_name="res.partner", readonly=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("design", "Design"),
            ("test", "Test"),
            ("ready", "Ready"),
            ("production", "Production"),
        ],
        string="State",
        default="draft",
        readonly=True,
    )

    date_start_bbp = fields.Date(string="Start BBP", help="Start date business blueprint", readonly=True)
    date_end_bbp = fields.Date(string="End BBP", help="End date business blueprint", readonly=True)
    completion_bbp = fields.Float(string="Completion", help="Completion business blueprint", readonly=True)

    transaction_id = fields.Many2one(string="Transaction", comodel_name="business.transaction", readonly=True)
    transaction_type = fields.Selection(
        [
            ("md", "Master Data"),
            ("tr", "Transaction"),
            ("rp", "Report"),
            ("ex", "Extern"),
        ],
        string="Transaction Type",
        readonly=True,
    )

    responsible_step_id = fields.Many2one(string="Responsible Step", comodel_name="res.partner", readonly=True)
    role_id = fields.Many2one(string="Role", comodel_name="business.role", readonly=True)

    @property
    def _table_query(self):
        return f"{self._select()} {self._from()} {self._where()}"

    @api.model
    def _select(self):
        return """
            SELECT
                bps.id AS id,
                bp.id AS process_id,
                bp.project_id AS project_id,
                bps.id AS step_id,
                bps.sequence AS sequence,
                bp.area_id AS area_id,
                bp.process_group_id AS process_group_id,
                bp.responsible_id AS responsible_id,
                bp.customer_id AS customer_id,
                bp.state AS state,

                bp.date_start_bbp AS date_start_bbp,
                bp.date_end_bbp AS date_end_bbp,
                bp.completion_bbp AS completion_bbp,

                bps.transaction_id AS transaction_id,
                bt.transaction_type AS transaction_type,
                bps.responsible_id AS responsible_step_id,
                bps.role_id AS role_id

        """

    @api.model
    def _from(self):
        return """
            FROM
                business_process bp
            JOIN business_process_step bps ON bp.id = bps.process_id
            LEFT JOIN business_transaction bt ON bps.transaction_id = bt.id
        """

    @api.model
    def _where(self):
        return """

        """
