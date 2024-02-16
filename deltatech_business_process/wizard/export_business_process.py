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
    state = fields.Selection([("choose", "choose"), ("get", "get")], default="choose")  # choose period  # get the file

    def do_export(self):
        active_ids = self.env.context.get("active_ids", [])
        active_model = self.env.context.get("active_model", "business.process")
        business_processes = self.env[active_model].browse(active_ids)
        # generez un json cu datele din business_processes si din pasii de process
        data = []
        for process in business_processes:
            process_data = {
                "name": process.name,
                "code": process.code,
                "description": process.description,
                "area": process.area_id.name,
                "process_group": process.process_group_id.name,
                "steps": [],
            }

            for step in process.step_ids:
                step_data = {
                    "name": step.name,
                    "code": step.code,
                    "description": step.description,
                    "area": step.area_id.name,
                    "sequence": step.sequence,
                    "transaction": step.transaction_id.name,
                    "details": step.details,
                }
                process_data["steps"].append(step_data)
            data.append(process_data)

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
