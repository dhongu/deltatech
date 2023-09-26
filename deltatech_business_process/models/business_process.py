# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models


class BusinessProcess(models.Model):
    _name = "business.process"
    _description = "Business process"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Name",
        required=True,
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    code = fields.Char(
        string="Code",
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    description = fields.Text(string="Description")
    area_id = fields.Many2one(
        string="Area",
        comodel_name="business.area",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    process_group_id = fields.Many2one(
        string="Process Group",
        comodel_name="business.process.group",
        domain="[('area_id', '=', area_id)]",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    step_ids = fields.One2many(
        string="Steps",
        comodel_name="business.process.step",
        inverse_name="process_id",
        copy=True,
        readonly=True,
        states={"draft": [("readonly", False)], "design": [("readonly", False)]},
    )

    responsible_id = fields.Many2one(
        string="Responsible",
        domain="[('is_company', '=', False)]",
        comodel_name="res.partner",
        readonly=True,
        states={"draft": [("readonly", False)], "design": [("readonly", False)]},
    )
    customer_id = fields.Many2one(
        string="Customer Responsible",
        domain="[('is_company', '=', False)]",
        comodel_name="res.partner",
        readonly=True,
        states={"draft": [("readonly", False)], "design": [("readonly", False)]},
    )
    state = fields.Selection(
        [("draft", "Draft"), ("design", "Design"), ("test", "Test"), ("ready", "Ready"), ("production", "Production")],
        string="State",
        default="draft",
        tracking=True,
        copy=False,
        index=True,
    )

    test_ids = fields.One2many(string="Tests", comodel_name="business.process.test", inverse_name="process_id")
    project_id = fields.Many2one(
        string="Project",
        comodel_name="business.project",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    development_ids = fields.Many2many("business.development", string="Developments", compute="_compute_developments")

    count_steps = fields.Integer(string="Count Steps", compute="_compute_count_steps")
    count_tests = fields.Integer(string="Count Tests", compute="_compute_count_tests")
    count_developments = fields.Integer(string="Count Developments", compute="_compute_count_developments")

    doc_count = fields.Integer(
        string="Count Documents", help="Number of documents attached", compute="_compute_attached_docs_count"
    )

    date_start_bbp = fields.Date(
        string="Start BBP",
        help="Start date business blueprint",
        readonly=True,
        states={"draft": [("readonly", False)], "design": [("readonly", False)]},
    )

    date_end_bbp = fields.Date(
        string="End BBP",
        help="End date business blueprint",
        readonly=True,
        states={"draft": [("readonly", False)], "design": [("readonly", False)]},
    )
    completion_bbp = fields.Float(
        string="Completion",
        help="Completion business blueprint",
        readonly=True,
        states={"draft": [("readonly", False)], "design": [("readonly", False)]},
        group_operator="avg",
    )
    approved_id = fields.Many2one(
        string="Approved by",
        comodel_name="res.partner",
        readonly=True,
        states={"draft": [("readonly", False)], "design": [("readonly", False)]},
    )

    status_internal_test = fields.Selection(
        [("not_started", "Not started"), ("in_progress", "In progress"), ("done", "Done")],
        string="Status internal test",
        default="not_started",
    )
    status_integration_test = fields.Selection(
        [("not_started", "Not started"), ("in_progress", "In progress"), ("done", "Done")],
        string="Status integration test",
        default="not_started",
    )
    status_user_acceptance_test = fields.Selection(
        [("not_started", "Not started"), ("in_progress", "In progress"), ("done", "Done")],
        string="Status user acceptance test",
        default="not_started",
    )

    @api.model
    def create(self, vals):
        if not vals.get("code", False):
            vals["code"] = self.env["ir.sequence"].next_by_code(self._name)
        result = super().create(vals)
        return result

    def name_get(self):
        self.browse(self.ids).read(["name", "code"])
        return [
            (process.id, "{}{}".format(process.code and "[%s] " % process.code or "", process.name)) for process in self
        ]

    def _compute_developments(self):
        for process in self:
            process.development_ids = process.step_ids.mapped("development_ids")

    def _compute_count_developments(self):
        for process in self:
            process.count_developments = len(process.development_ids)

    def _compute_count_steps(self):
        for process in self:
            process.count_steps = len(process.step_ids)

    def _compute_count_tests(self):
        for process in self:
            process.count_tests = len(process.test_ids)

    def action_view_steps(self):
        domain = [("process_id", "=", self.id)]
        context = {
            "default_process_id": self.id,
            "default_sequence": len(self.step_ids) + 10,
            "default_responsible_id": self.responsible_id.id,
        }
        action = self.env["ir.actions.actions"]._for_xml_id("deltatech_business_process.action_business_process_step")
        action.update({"domain": domain, "context": context})
        return action

    def action_view_tests(self):
        domain = [("process_id", "=", self.id)]
        context = {
            "default_process_id": self.id,
        }
        action = self.env["ir.actions.actions"]._for_xml_id("deltatech_business_process.action_business_process_test")
        action.update({"domain": domain, "context": context})
        return action

    def action_view_developments(self):
        domain = [("id", "=", self.development_ids.ids)]
        context = {
            "default_project_id": self.id,
        }
        action = self.env["ir.actions.actions"]._for_xml_id("deltatech_business_process.action_business_development")
        action.update({"domain": domain, "context": context})
        return action

    def get_attachment_domain(self):
        domain = [("res_model", "=", "business.process"), ("res_id", "=", self.id)]
        return domain

    def _compute_attached_docs_count(self):
        for order in self:
            domain = order.get_attachment_domain()
            order.doc_count = self.env["ir.attachment"].search_count(domain)

    def attachment_tree_view(self):
        domain = self.get_attachment_domain()
        return {
            "name": _("Attachments"),
            "domain": domain,
            "res_model": "ir.attachment",
            "type": "ir.actions.act_window",
            "view_id": False,
            "view_mode": "kanban,tree,form",
            "context": "{{'default_res_model': '{}','default_res_id': {}}}".format(self._name, self.id),
        }

    def _load_records(self, data_list, update=False):
        project_id = self.env.context.get("default_project_id", False)
        for data in data_list:
            code = data["values"].get("code", False)
            if code:
                domain = [("project_id", "=", project_id), ("code", "=", code)]
                record = self.search(domain, limit=1)
                if record:
                    data["values"]["id"] = record.id
                else:
                    data["values"]["id"] = False

        return super()._load_records(data_list, update)

    @api.model
    def _name_search(self, name="", args=None, operator="ilike", limit=100, name_get_uid=None):
        if args is None:
            args = []
        project_id = self.env.context.get("default_project_id", False)
        domain = [("code", "=", name)]
        if project_id:
            domain.append(("project_id", "=", project_id))
        ids = list(self._search(domain + args, limit=limit))

        search_domain = [("name", operator, name)]
        if ids:
            search_domain.append(("id", "not in", ids))
        ids += list(self._search(search_domain + args, limit=limit))

        return ids

    def _start_test(self, scope):
        for process in self:
            domain = [("process_id", "=", process.id), ("scope", "=", scope)]
            test = self.env["business.process.test"].search(domain, limit=1)
            if not test:
                test = self.env["business.process.test"].create(
                    {
                        "name": _("Test %s") % process.code if process.code else process.name,
                        "process_id": process.id,
                        "tester_id": process.responsible_id.id,
                        "scope": scope,
                    }
                )
                test._onchange_process_id()

    def _add_followers(self):
        for process in self:
            followers = self.env["res.partner"]
            if process.responsible_id not in process.message_partner_ids:
                followers |= process.responsible_id
            if process.customer_id not in process.message_partner_ids:
                followers |= process.customer_id
            for step in process.step_ids:
                if step.responsible_id not in process.message_partner_ids:
                    followers |= step.responsible_id
            process.message_subscribe(followers.ids)

    def button_start_design(self):
        self._add_followers()
        for process in self:
            values = {"state": "design"}
            if not process.date_start_bbp:
                values["date_start_bbp"] = fields.Date.today()
            process.write(values)

    def button_start_test(self):
        self._add_followers()
        for process in self:
            values = {"state": "test"}
            if not process.date_end_bbp:
                values["date_end_bbp"] = fields.Date.today()
            if not process.completion_bbp:
                values["completion_bbp"] = 100.0
            process.write(values)

    def button_end_test(self):
        # se verifica daca toate testele sunt finalizate
        self.write({"state": "ready"})

    def button_go_live(self):
        self.write({"state": "production"})

    def button_draft(self):
        self.write({"state": "draft"})

    def start_internal_test(self):
        self._start_test("internal")

    def start_integration_test(self):
        self._start_test("integration")

    def start_user_acceptance_test(self):
        self._start_test("user_acceptance")
