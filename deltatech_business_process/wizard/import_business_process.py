# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


import base64
import json

from odoo import _, fields, models
from odoo.exceptions import UserError


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
        for process_data in data:
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

            domain = [("code", "=", process_data["code"]), ("project_id", "=", project.id)]

            process = self.env["business.process"].search(domain, limit=1)
            if not process:
                process = self.env["business.process"].create(
                    {
                        "name": process_data["name"],
                        "code": process_data["code"],
                        "description": process_data["description"],
                        "area_id": area.id,
                        "process_group_id": process_group.id,
                        "project_id": project.id,
                        "responsible_id": responsible.id,
                        "customer_id": customer.id,
                        "approved_id": approves.id,
                        "date_start_bbp": process_data["date_start_bbp"],
                        "date_end_bbp": process_data["date_end_bbp"],
                        "state": process_data["state"],
                    }
                )
            else:
                process.write(
                    {
                        "name": process_data["name"],
                        "code": process_data["code"],
                        "description": process_data["description"],
                        "area_id": area.id,
                        "process_group_id": process_group.id,
                        "responsible_id": responsible.id,
                        "customer_id": customer.id,
                        "approved_id": approves.id,
                        "date_start_bbp": process_data["date_start_bbp"],
                        "date_end_bbp": process_data["date_end_bbp"],
                        "state": process_data["state"],
                    }
                )

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
                    self.env["business.process.step"].create(
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
            if process_data["include_tests"]:
                for test_data in process_data["tests"]:
                    tester = self.env["res.partner"]
                    if process_data["responsible"]:
                        tester = self.env["res.partner"].search([("name", "=", test_data["tester"])], limit=1)
                        if not tester:
                            tester = self.env["res.partner"].create({"name": process_data["responsible"]})
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
                                }
                            )

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
