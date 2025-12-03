# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


import base64
import json

from odoo import fields, models


class BusinessProcessExport(models.TransientModel):
    _name = "business.process.export"
    _description = "Business Process Export"

    name = fields.Char(string="File Name", readonly=True)
    data_file = fields.Binary(string="File", readonly=True)
    include_tests = fields.Boolean(string="Include Tests in Export?")
    include_responsible = fields.Boolean(string="Include Responsible?")
    include_customer_responsible = fields.Boolean(string="Include Customer Responsible?")
    include_approved_by = fields.Boolean(string="Include Approved By?")
    include_support = fields.Boolean(string="Include Support?")
    include_durations = fields.Boolean(string="Include Durations?")
    include_process_state = fields.Boolean(string="Include Process State?")
    include_modules = fields.Boolean(string="Include Modules?")
    include_issues = fields.Boolean(string="Include Issues?")
    include_developments = fields.Boolean(string="Include Developments?")
    state = fields.Selection([("choose", "choose"), ("get", "get")], default="choose")  # choose period  # get the file

    def do_export(self):
        active_ids = self.env.context.get("active_ids", [])
        active_model = self.env.context.get("active_model", "business.process")
        business_processes = self.env[active_model].browse(active_ids)
        # generez un json cu datele din business_processes si din pasii de process
        data = {"developments": [], "issues": [], "processes": []}

        if self.include_developments:
            projects = business_processes.mapped("project_id")
            project_ids = projects.ids
            developments = self.env["business.development"].search([("project_id", "in", project_ids)])
            for development in developments:
                development_data = {
                    "name": development.name,
                    "code": development.code,
                    "description": development.description,
                    "area": development.area_id.name,
                    "type": development.type_id.name,
                    "approved": development.approved,
                    "state": development.state,
                    "date_start_fs": development.date_start_fs,
                    "date_end_fs": development.date_end_fs,
                    "completion_fs": development.completion_fs,
                    "effort_fs": development.effort_fs,
                    "date_start_dev": development.date_start_dev,
                    "date_end_dev": development.date_end_dev,
                    "completion_dev": development.completion_dev,
                    "effort_dev": development.effort_dev,
                    "date_start_test": development.date_start_test,
                    "date_end_test": development.date_end_test,
                    "completion_test": development.completion_test,
                    "effort_test": development.effort_test,
                    "development_duration": development.development_duration,
                    "note": development.note,
                }
                data["developments"].append(development_data)

        if self.include_issues:
            projects = business_processes.mapped("project_id")
            project_ids = projects.ids
            issues = self.env["business.issue"].search([("project_id", "in", project_ids)])
            for issue in issues:
                issue_data = {
                    "name": issue.name,
                    "code": issue.code,
                    "description": issue.description,
                    "project": issue.project_id.name,
                    "process": issue.process_id.name,
                    "step_test": issue.step_test_id.name,
                    "category": issue.category,
                    "open_date": issue.open_date,
                    "date_estimated": issue.date_estimated,
                    "solution": issue.solution,
                    "solution_date": issue.solution_date,
                    "closed_date": issue.closed_date,
                    "area": issue.area_id.name,
                    "state": issue.state,
                    "severity": issue.severity,
                }
                data["issues"].append(issue_data)

        for process in business_processes:
            process_data = {
                "name": process.name,
                "code": process.code,
                "description": process.description,
                "area": process.area_id.name,
                "process_group": process.process_group_id.name,
                "steps": [],
                "include_tests": self.include_tests,
                "include_durations": self.include_durations,
                "include_modules": self.include_modules,
                "tests": [],
                "responsible": "",
                "customer": "",
                "approved": "",
                "support": "",
                "configuration_duration": "",
                "instructing_duration": "",
                "data_migration_duration": "",
                "testing_duration": "",
                "duration_for_completion": "",
                "date_start_bbp": process.date_start_bbp,
                "date_end_bbp": process.date_end_bbp,
                "state": (process.state if self.include_process_state else "draft"),
                "module_type": process.module_type,
                "implementation_stage": process.implementation_stage,
            }
            if self.include_durations:
                process_data["configuration_duration"] = process.configuration_duration
                process_data["instructing_duration"] = process.instructing_duration
                process_data["data_migration_duration"] = process.data_migration_duration
                process_data["testing_duration"] = process.testing_duration
                process_data["duration_for_completion"] = process.duration_for_completion
            if self.include_responsible:
                process_data["responsible"] = process.responsible_id.name
            if self.include_customer_responsible:
                process_data["customer"] = process.customer_id.name
            if self.include_approved_by:
                process_data["approved"] = process.approved_id.name
            if self.include_support:
                process_data["support"] = process.support_id.name
            if self.include_modules:
                process_data["modules"] = [module.name for module in process.module_ids]
            for step in process.step_ids:
                step_data = {
                    "name": step.name,
                    "code": step.code,
                    "area": step.area_id.name,
                    "description": step.description,
                    "sequence": step.sequence,
                    "transaction": step.transaction_id.name,
                    "details": step.details,
                    "development_ids": [],
                }
                if self.include_developments:
                    for step_development in step.development_ids:
                        step_data["development_ids"].append(step_development.code or step_development.name)
                process_data["steps"].append(step_data)
            if self.include_tests:
                process_data["status_internal_test"] = process.status_internal_test
                process_data["status_integration_test"] = process.status_integration_test
                process_data["status_user_acceptance_test"] = process.status_user_acceptance_test
                for test in process.test_ids:
                    test_data = {
                        "name": test.name,
                        "process_id": test.process_id.name,
                        "scope": test.scope,
                        "tester": test.tester_id.name,
                        "date_start": test.date_start,
                        "date_end": test.date_end,
                        "state": test.state,
                        "test_steps": [],
                    }

                    for test_step in test.test_step_ids:
                        test_step_data = {
                            "name": test_step.name,
                            "transaction": test_step.transaction_id.name,
                            "step": test_step.step_id.name,
                            "test": test_step.process_test_id.name,
                            "result": test_step.result,
                            "test_started": test_step.test_started,
                            "responsible": test_step.responsible_id.name,
                        }
                        test_data["test_steps"].append(test_step_data)

                    process_data["tests"].append(test_data)

            data["processes"].append(process_data)

        json_data = json.dumps(data, indent=4, sort_keys=True, default=str)
        self.write(
            {
                "state": "get",
                "name": "business_process_export.json",
                "data_file": base64.b64encode(json_data.encode("utf-8")),
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "view_type": "form",
            "res_id": self.id,
            "views": [(False, "form")],
            "target": "new",
        }

    def do_back(self):
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
