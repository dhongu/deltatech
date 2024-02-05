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
                area = self.env["business.area"].search([("name", "=", process_data["area"])])
                if not area:
                    area = self.env["business.area"].create({"name": process_data["area"]})
            process_group = self.env["business.process.group"]
            if process_data["process_group"]:
                process_group = self.env["business.process.group"].search(
                    [("name", "=", process_data["process_group"])]
                )
                if not process_group:
                    process_group = self.env["business.process.group"].create({"name": process_data["process_group"]})
            if process_data["responsible_id"]:
                responsible = self.env["res.partner"].search([("name", "=", process_data["responsible_id"])])
                if not responsible:
                    responsible = self.env["res.partner"].create({"name": process_data["responsible_id"]})
            if process_data["customer_id"]:
                customer = self.env["res.partner"].search([("name", "=", process_data["customer_id"])])
                if not customer:
                    customer = self.env["res.partner"].create({"name": process_data["customer_id"]})
            if process_data["approved_id"]:
                approves = self.env["res.partner"].search([("name", "=", process_data["approved_id"])])
                if not approves:
                    approves = self.env["res.partner"].create({"name": process_data["approved_id"]})

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
                    area = self.env["business.area"].search([("name", "=", step_data["area"])])
                    if not area:
                        area = self.env["business.area"].create({"name": step_data["area"]})
                transaction = self.env["business.transaction"]
                if step_data["transaction"]:
                    transaction = self.env["business.transaction"].search([("name", "=", step_data["transaction"])])
                    if not transaction:
                        transaction = self.env["business.transaction"].create({"name": step_data["transaction"]})
                if step_data["responsible"]:
                    step_responsible = self.env["res.partner"].search([("name", "=", step_data["responsible"])])
                    if not step_responsible:
                        step_responsible = self.env["res.partner"].create({"name": step_data["responsible"]})

                domain = [("code", "=", step_data["code"]), ("process_id", "=", process.id)]
                step = self.env["business.process.step"].search(domain, limit=1)
                if not step:
                    self.env["business.process.step"].create(
                        {
                            "name": step_data["name"],
                            "code": step_data["code"],
                            "description": step_data["description"],
                            "area_id": area.id,
                            "transaction_id": transaction.id,
                            "details": step_data["details"],
                            "sequence": step_data["sequence"],
                            "process_id": process.id,
                            "responsible_id": step_responsible.id,
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
                            "responsible_id": step_responsible.id,
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
