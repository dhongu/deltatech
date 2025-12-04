# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


import base64
import html as _html
import json

# Helper to normalize descriptions coming from JSON (may contain HTML)
import re

from odoo import _, fields, models
from odoo.exceptions import UserError


def _normalize_description(value):
    if not value:
        return ""
    if isinstance(value, str):
        # Strip HTML tags and unescape entities
        text = _html.unescape(re.sub(r"<[^>]*>", "", value))
        return text.strip()
    return str(value)


class BusinessProcessImport(models.TransientModel):
    _name = "business.process.import"
    _description = "Business Process Import"

    name = fields.Char(string="File Name")
    data_file = fields.Binary(string="File")
    state = fields.Selection([("choose", "choose"), ("get", "get")], default="get")  # choose period  # get the file

    def do_import(self):
        active_ids = self.env.context.get("active_ids", [])
        active_model = self.env.context.get("active_model", "business.project")
        project = self.env["business.project"]

        if active_model == "business.project":
            project = self.env[active_model].browse(active_ids)
        if active_model == "business.process":
            process = self.env[active_model].browse(active_ids)
            project = process[0].project_id

        if not project:
            raise UserError(_("No project selected!"))

        data = base64.b64decode(self.data_file.decode("utf-8"))
        data = json.loads(data)
        self.import_developments(data, project)
        for process_data in data["processes"]:
            area = self.env["business.area"]
            if process_data["area"]:
                area = self.env["business.area"].search([("name", "=", process_data["area"])], limit=1)
                if not area:
                    area = self.env["business.area"].create({"name": process_data["area"]})
            process_group = self.env["business.process.group"]
            if process_data["process_group"]:
                process_group = self.env["business.process.group"].search(
                    [("name", "=", process_data["process_group"])], limit=1
                )
                if not process_group:
                    process_group = self.env["business.process.group"].create({"name": process_data["process_group"]})
            responsible = self.env["res.partner"]
            if process_data["responsible"]:
                responsible = self.env["res.partner"].search([("name", "=", process_data["responsible"])], limit=1)
                if not responsible:
                    responsible = self.env["res.partner"].create({"name": process_data["responsible"]})
            customer = self.env["res.partner"]
            if process_data["customer"]:
                customer = self.env["res.partner"].search([("name", "=", process_data["customer"])], limit=1)
                if not customer:
                    customer = self.env["res.partner"].create({"name": process_data["customer"]})
            approves = self.env["res.partner"]
            if process_data["approved"]:
                approves = self.env["res.partner"].search([("name", "=", process_data["approved"])], limit=1)
                if not approves:
                    approves = self.env["res.partner"].create({"name": process_data["approved"]})
            support = self.env["res.partner"]
            if process_data["support"]:
                support = self.env["res.partner"].search([("name", "=", process_data["support"])], limit=1)
                if not support:
                    support = self.env["res.partner"].create({"name": process_data["support"]})
            domain = [("code", "=", process_data["code"]), ("project_id", "=", project.id)]
            configuration_duration = 0.0
            instructing_duration = 0.0
            data_migration_duration = 0.0
            testing_duration = 0.0
            duration_for_completion = 0.0
            if "include_durations" in process_data and process_data["include_durations"]:
                configuration_duration = process_data["configuration_duration"]
                instructing_duration = process_data["instructing_duration"]
                data_migration_duration = process_data["data_migration_duration"]
                testing_duration = process_data["testing_duration"]
                duration_for_completion = process_data["duration_for_completion"]

            process = self.env["business.process"].search(domain, limit=1)
            if not process:
                process = self.env["business.process"].create(
                    {
                        "name": process_data["name"],
                        "code": process_data["code"],
                        "description": _normalize_description(process_data.get("description")),
                        "area_id": area.id,
                        "process_group_id": process_group.id,
                        "project_id": project.id,
                        "responsible_id": responsible.id,
                        "support_id": support.id,
                        "customer_id": customer.id,
                        "approved_id": approves.id,
                        "date_start_bbp": process_data["date_start_bbp"],
                        "date_end_bbp": process_data["date_end_bbp"],
                        "state": process_data["state"],
                        "implementation_stage": process_data["implementation_stage"],
                        "module_type": process_data["module_type"],
                        "configuration_duration": configuration_duration,
                        "instructing_duration": instructing_duration,
                        "data_migration_duration": data_migration_duration,
                        "testing_duration": testing_duration,
                        "duration_for_completion": duration_for_completion,
                        "status_internal_test": (
                            process_data["status_internal_test"]
                            if "status_internal_test" in process_data
                            else "not_started"
                        ),
                        "status_integration_test": (
                            process_data["status_integration_test"]
                            if "status_integration_test" in process_data
                            else "not_started"
                        ),
                        "status_user_acceptance_test": (
                            process_data["status_user_acceptance_test"]
                            if "status_user_acceptance_test" in process_data
                            else "not_started"
                        ),
                    }
                )
            else:
                process.write(
                    {
                        "name": process_data["name"],
                        "code": process_data["code"],
                        "description": _normalize_description(process_data.get("description")),
                        "area_id": area.id,
                        "process_group_id": process_group.id,
                        "responsible_id": responsible.id,
                        "support_id": support.id,
                        "customer_id": customer.id,
                        "approved_id": approves.id,
                        "date_start_bbp": process_data["date_start_bbp"],
                        "date_end_bbp": process_data["date_end_bbp"],
                        "state": process_data["state"],
                        "implementation_stage": process_data["implementation_stage"],
                        "module_type": process_data["module_type"],
                    }
                )
            self.import_modules(process_data, process)
            self.import_steps(process_data, process)
            self.import_test(process_data, process)
        self.import_issues(data, project)
        self.write({"state": "choose"})
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "view_type": "form",
            "res_id": self.id,
            "views": [(False, "form")],
            "target": "new",
        }

    def import_developments(self, data, project):
        for development_data in data["developments"]:
            area = self.env["business.area"]
            type_dev = self.env["business.development.type"]
            if development_data["area"]:
                area = self.env["business.area"].search([("name", "=", development_data["area"])], limit=1)
                if not area:
                    area = self.env["business.area"].create({"name": development_data["area"]})
            if development_data["type"]:
                type_dev = self.env["business.development.type"].search(
                    [("name", "=", development_data["type"])], limit=1
                )
                if not type_dev:
                    type_dev = self.env["business.development.type"].create({"name": development_data["type"]})
            domain = [("code", "=", development_data["code"]), ("project_id", "=", project.id)]
            development = self.env["business.development"].search(domain, limit=1)
            if not development:
                self.env["business.development"].create(
                    {
                        "name": development_data["name"],
                        "code": development_data["code"],
                        "description": development_data.get("description"),
                        "area_id": area.id,
                        "type_id": type_dev.id,
                        "project_id": project.id,
                        "approved": development_data["approved"],
                        "state": development_data["state"],
                        "date_start_fs": development_data["date_start_fs"],
                        "date_end_fs": development_data["date_end_fs"],
                        "completion_fs": development_data["completion_fs"],
                        "effort_fs": development_data["effort_fs"],
                        "date_start_dev": development_data["date_start_dev"],
                        "date_end_dev": development_data["date_end_dev"],
                        "completion_dev": development_data["completion_dev"],
                        "effort_dev": development_data["effort_dev"],
                        "date_start_test": development_data["date_start_test"],
                        "date_end_test": development_data["date_end_test"],
                        "completion_test": development_data["completion_test"],
                        "effort_test": development_data["effort_test"],
                        "development_duration": development_data["development_duration"],
                        "note": development_data["note"],
                    }
                )
            else:
                development.write(
                    {
                        "name": development_data["name"],
                        "code": development_data["code"],
                        "description": development_data.get("description"),
                        "area_id": area.id,
                        "type_id": type_dev.id,
                        "approved": development_data["approved"],
                        "state": development_data["state"],
                        "date_start_fs": development_data["date_start_fs"],
                        "date_end_fs": development_data["date_end_fs"],
                        "completion_fs": development_data["completion_fs"],
                        "effort_fs": development_data["effort_fs"],
                        "date_start_dev": development_data["date_start_dev"],
                        "date_end_dev": development_data["date_end_dev"],
                        "completion_dev": development_data["completion_dev"],
                        "effort_dev": development_data["effort_dev"],
                        "date_start_test": development_data["date_start_test"],
                        "date_end_test": development_data["date_end_test"],
                        "completion_test": development_data["completion_test"],
                        "effort_test": development_data["effort_test"],
                        "development_duration": development_data["development_duration"],
                        "note": development_data["note"],
                    }
                )

    def import_issues(self, data, project):
        for issue in data["issues"]:
            area = self.env["business.area"]
            if issue["area"]:
                area = self.env["business.area"].search([("name", "=", issue["area"])], limit=1)
                if not area:
                    area = self.env["business.area"].create({"name": issue["area"]})
            domain = [("code", "=", issue["code"]), ("project_id", "=", project.id)]
            issue_rec = self.env["business.issue"].search(domain, limit=1)
            process = self.env["business.process"]
            if issue["process"]:
                process = self.env["business.process"].search(
                    [("name", "=", issue["process"]), ("project_id", "=", project.id)], limit=1
                )
            step_test = self.env["business.process.step.test"]
            if issue["step_test"]:
                if not issue["process"]:
                    raise UserError(_("We have steps on issues without process"))
                step_test = self.env["business.process.step.test"].search(
                    [("name", "=", issue["step_test"]), ("process_id", "=", process.id)],
                    limit=1,
                )
            if not issue_rec:
                issue_rec = self.env["business.issue"].create(
                    {
                        "name": issue["name"],
                        "code": issue["code"],
                        "description": issue.get("description"),
                        "project_id": project.id,
                        "process_id": process.id,
                        "step_test_id": step_test.id,
                        "category": issue["category"],
                        "open_date": issue["open_date"],
                        "date_estimated": issue["date_estimated"],
                        "solution": issue["solution"],
                        "solution_date": issue["solution_date"],
                        "closed_date": issue["closed_date"],
                        "area_id": area.id,
                        "state": issue["state"],
                        "severity": issue["severity"],
                    }
                )
            else:
                issue_rec.write(
                    {
                        "name": issue["name"],
                        "code": issue["code"],
                        "description": issue.get("description"),
                        "project_id": project.id,
                        "process_id": process.id,
                        "step_test_id": step_test.id,
                        "category": issue["category"],
                        "open_date": issue["open_date"],
                        "date_estimated": issue["date_estimated"],
                        "solution": issue["solution"],
                        "solution_date": issue["solution_date"],
                        "closed_date": issue["closed_date"],
                        "area_id": area.id,
                        "state": issue["state"],
                        "severity": issue["severity"],
                    }
                )
            if step_test:
                step_test.issue_ids = [(4, issue_rec.id)]

    def import_modules(self, process_data, process):
        if "include_modules" in process_data and process_data["include_modules"]:
            for module in process_data["modules"]:
                module = self.env["ir.module.module"].search([("name", "=", module)], limit=1)
                if module:
                    process.module_ids = [(4, module.id)]

    def import_steps(self, process_data, process):
        for step_data in process_data["steps"]:
            area = self.env["business.area"]
            if step_data["area"]:
                area = self.env["business.area"].search([("name", "=", step_data["area"])], limit=1)
                if not area:
                    area = self.env["business.area"].create({"name": step_data["area"]})
            transaction = self.env["business.transaction"]
            if step_data["transaction"]:
                transaction = self.env["business.transaction"].search(
                    [("name", "=", step_data["transaction"])], limit=1
                )
                if not transaction:
                    transaction = self.env["business.transaction"].create({"name": step_data["transaction"]})

            domain = [("code", "=", step_data["code"]), ("process_id", "=", process.id)]
            step = self.env["business.process.step"].search(domain, limit=1)
            if not step:
                step = self.env["business.process.step"].create(
                    {
                        "name": step_data["name"],
                        "code": step_data["code"],
                        "area_id": area.id,
                        "description": step_data["description"],
                        "transaction_id": transaction.id,
                        "details": step_data["details"],
                        "sequence": step_data["sequence"],
                        "process_id": process.id,
                    }
                )
            else:
                step.write(
                    {
                        "name": step_data["name"],
                        "code": step_data["code"],
                        "description": step_data["description"],
                        "area_id": area.id,
                        "transaction_id": transaction.id,
                        "details": step_data["details"],
                        "sequence": step_data["sequence"],
                        "process_id": process.id,
                    }
                )
            for development in step_data.get("development_ids", []):
                development_rec = self.env["business.development"].search(
                    [("code", "=", development), ("project_id", "=", process.project_id.id)], limit=1
                )
                if development_rec:
                    step.development_ids = [(4, development_rec.id)]
                else:
                    development_rec = self.env["business.development"].search(
                        [("name", "=", development), ("project_id", "=", process.project_id.id)], limit=1
                    )
                    if development_rec:
                        step.development_ids = [(4, development_rec.id)]

    def import_test(self, process_data, process):
        if process_data["include_tests"]:
            for test_data in process_data["tests"]:
                tester = self.env["res.partner"]
                if test_data["tester"]:
                    tester = self.env["res.partner"].search([("name", "=", test_data["tester"])], limit=1)
                    if not tester:
                        tester = self.env["res.partner"].create({"name": test_data["tester"]})
                domain = [("name", "=", test_data["name"]), ("process_id", "=", process.id)]
                test = self.env["business.process.test"].search(domain, limit=1)
                if not test:
                    self.env["business.process.test"].create(
                        {
                            "name": test_data["name"],
                            "process_id": process.id,
                            "tester_id": tester.id,
                            "scope": test_data["scope"],
                            "date_start": test_data["date_start"],
                            "date_end": test_data["date_end"],
                            "state": test_data["state"],
                        }
                    )
                else:
                    test.write(
                        {
                            "name": test_data["name"],
                            "process_id": process.id,
                            "tester_id": tester,
                            "scope": test_data["scope"],
                            "date_start": test_data["date_start"],
                            "date_end": test_data["date_end"],
                            "state": test_data["state"],
                        }
                    )
                for step_test_data in test_data["test_steps"]:
                    transaction = self.env["business.transaction"]
                    if step_test_data["transaction"]:
                        transaction = self.env["business.transaction"].search(
                            [("name", "=", step_test_data["transaction"])], limit=1
                        )
                        if not transaction:
                            transaction = self.env["business.transaction"].create(
                                {"name": step_test_data["transaction"]}
                            )
                    step_in_test = self.env["business.transaction"]
                    if step_test_data["step"]:
                        step_in_test = self.env["business.process.step"].search(
                            [("name", "=", step_test_data["step"]), ("process_id", "=", process.id)], limit=1
                        )
                    test_of_step = self.env["business.process.test"]
                    if step_test_data["test"]:
                        test_of_step = self.env["business.process.test"].search(
                            [("name", "=", step_test_data["test"]), ("process_id", "=", process.id)], limit=1
                        )
                    responsible = self.env["res.partner"]
                    if "responsible" in step_test_data and step_test_data["responsible"]:
                        responsible = self.env["res.partner"].search(
                            [("name", "=", step_test_data["responsible"])], limit=1
                        )
                        if not responsible:
                            responsible = self.env["res.partner"].create({"name": step_test_data["responsible"]})
                    domain = [("name", "=", step_test_data["name"]), ("process_test_id", "=", test_of_step.id)]
                    step_test = self.env["business.process.step.test"].search(domain, limit=1)
                    if not step_test:
                        self.env["business.process.step.test"].create(
                            {
                                "name": step_test_data["name"],
                                "process_id": process.id,
                                "transaction_id": transaction.id,
                                "step_id": step_in_test.id,
                                "process_test_id": test_of_step.id,
                                "result": step_test_data["result"] if "result" in step_test_data else "draft",
                                "test_started": (
                                    step_test_data["test_started"] if "test_started" in step_test_data else True
                                ),
                                "responsible_id": responsible.id,
                            }
                        )
                    else:
                        step_test.write(
                            {
                                "name": step_test_data["name"],
                                "process_id": process.id,
                                "transaction_id": transaction.id,
                                "step_id": step_in_test.id,
                                "process_test_id": test_of_step.id,
                                "result": step_test_data["result"] if "result" in step_test_data else "draft",
                                "test_started": (
                                    step_test_data["test_started"] if "test_started" in step_test_data else True
                                ),
                                "responsible_id": responsible.id,
                            }
                        )

    def do_back(self):
        self.write({"state": "get"})
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "view_type": "form",
            "res_id": self.id,
            "views": [(False, "form")],
            "target": "new",
        }
