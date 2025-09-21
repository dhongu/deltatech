# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class BusinessProcessTestReport(models.Model):
    _name = "business.process.test.report"
    _description = "Business process test report"
    _auto = False
    _order = "project_id,  process_test_id, process_step_test_id"

    project_id = fields.Many2one(string="Project", comodel_name="business.project", required=True)
    process_id = fields.Many2one("business.process", string="Business process", readonly=True)
    step_id = fields.Many2one(string="Step", comodel_name="business.process.step", readonly=True)
    process_test_id = fields.Many2one(string="Process Test", comodel_name="business.process.test", readonly=True)
    process_step_test_id = fields.Many2one(
        string="Process Step Test",
        comodel_name="business.process.step.test",
        readonly=True,
    )

    sequence = fields.Integer(string="Sequence", readonly=True)

    area_id = fields.Many2one(string="Area", comodel_name="business.area", readonly=True)
    process_group_id = fields.Many2one(string="Process Group", comodel_name="business.process.group", readonly=True)

    responsible_id = fields.Many2one(string="Responsible Process", comodel_name="res.partner", readonly=True)

    customer_id = fields.Many2one(string="Customer Responsible", comodel_name="res.partner", readonly=True)
    state_bp = fields.Selection(
        [
            ("draft", "Draft"),
            ("design", "Design"),
            ("test", "Test"),
            ("ready", "Ready"),
            ("production", "Production"),
        ],
        string="State BP",
        default="draft",
        readonly=True,
    )

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

    # Test
    state_test = fields.Selection(
        [("draft", "Draft"), ("run", "Run"), ("wait", "Waiting"), ("done", "Done")],
        string="State Test",
        default="draft",
        readonly=True,
    )
    scope = fields.Selection(
        [
            ("internal", "Internal"),
            ("integration", "Integration"),
            ("user_acceptance", "User Acceptance"),
            ("regression", "Regression"),
            ("other", "Other"),
        ],
        string="Scope",
        default="other",
        readonly=True,
    )
    completion_test = fields.Float(help="Completion test", aggregator="avg", readonly=True, digits=(16, 2))

    result = fields.Selection(
        [
            ("draft", "Draft"),
            ("passed", "Passed"),
            ("failed", "Failed"),
        ],
        string="Result",
        readonly=True,
    )

    data_used = fields.Text(string="Data used", readonly=True)
    data_result = fields.Text(string="Data result", readonly=True)

    date_start = fields.Date(string="Date start test", readonly=True)
    date_end = fields.Date(string="Date end test", readonly=True)

    count_issues = fields.Integer(string="Issues", readonly=True)

    @property
    def _table_query(self):
        return f"{self._select()} {self._from()} {self._where()} {self._order_by()}"

    @api.model
    def _select(self):
        return """
            SELECT
                bps.id AS id,
                bp.id AS process_id,
                bp.project_id AS project_id,
                bps.id AS step_id,
                bpt.id AS process_test_id,
                bpst.id AS process_step_test_id,
                bps.sequence AS sequence,
                bp.area_id AS area_id,
                bp.process_group_id AS process_group_id,
                bp.responsible_id AS responsible_id,
                bp.customer_id AS customer_id,
                bp.state AS state_bp,



                bps.transaction_id AS transaction_id,
                bt.transaction_type AS transaction_type,
                bpst.responsible_id AS responsible_step_id,
                bps.role_id AS role_id,

                bpt.state AS state_test,
                bpt.scope AS scope,
                bpt.completion_test AS completion_test,
                bpst.result AS result,

                bpst.data_used AS data_used,
                bpst.data_result AS data_result,
                bpst.date_start AS date_start,
                bpst.date_end AS date_end,
                bpst.count_issues AS count_issues


        """

    @api.model
    def _from(self):
        return """
            FROM business_process_step_test bpst

            JOIN  business_process_test bpt ON bpt.id = bpst.process_test_id
            JOIN business_process bp ON bp.id = bpt.process_id


            JOIN business_process_step bps ON bps.id = bpst.step_id
            LEFT JOIN business_transaction bt ON bpst.transaction_id = bt.id
        """

    @api.model
    def _where(self):
        return """

        """

    @api.model
    def _order_by(self):
        return """
            ORDER BY bp.project_id, bp.id,  bpt.id, bpst.id
        """
