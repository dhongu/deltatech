# ©  2023 Deltatech
# See README.rst file on addons root folder for license details
import base64
import io

import xlsxwriter

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# from odoo.tools import date_utils


class BusinessProject(models.Model):
    _name = "business.project"
    _description = "Business project"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    code = fields.Char(string="Code")
    name = fields.Char(string="Name", required=True)
    customer_id = fields.Many2one(string="Customer", comodel_name="res.partner")
    logo = fields.Image()
    state = fields.Selection(
        [
            ("preparation", "Preparation"),
            ("exploration", "Exploration"),
            ("realization", "Realization"),
            ("deployment", "Deployment"),
            ("running", "Running"),
            ("closed", "Closed"),
        ],
        string="State",
        default="preparation",
    )
    date_start = fields.Date(string="Start date")
    date_go_live = fields.Date(string="Go live date")
    process_ids = fields.One2many(string="Processes", comodel_name="business.process", inverse_name="project_id")

    issue_ids = fields.One2many(string="Issues", comodel_name="business.issue", inverse_name="project_id")

    count_processes = fields.Integer(string="Count Processes", compute="_compute_count_processes")
    count_issues = fields.Integer(string="Count Issues", compute="_compute_count_issues")
    count_steps = fields.Integer(string="Steps", compute="_compute_count_steps")
    count_developments = fields.Integer(string="Developments", compute="_compute_count_developments")

    responsible_id = fields.Many2one(
        string="Responsible",
        domain="[('is_company', '=', False)]",
        comodel_name="res.partner",
    )
    team_member_ids = fields.Many2many(string="Team members", comodel_name="res.partner")
    total_project_duration = fields.Float(string="Total project duration")
    doc_count = fields.Integer(
        string="Count Documents",
        help="Number of documents attached",
        compute="_compute_attached_docs_count",
    )
    project_manager_id = fields.Many2one(
        string="Project Manager",
        comodel_name="res.partner",
    )
    project_type = fields.Selection([("remote", "Remote"), ("local", "Local")], string="Project Type", default="remote")

    attachment_ids = fields.One2many(
        "ir.attachment",
        compute="_compute_attachment_ids",
        string="Main Attachments",
        help="Attachments that don't come from a message.",
    )

    @api.model
    def _get_attachments_search_domain(self, model, res_ids):
        return [("res_id", "in", res_ids), ("res_model", "=", model)]

    def _compute_attachment_ids(self):
        for project in self:
            domain = project._get_attachments_search_domain(project._name, project.ids)
            attachments = self.env["ir.attachment"].search(domain)
            attachments |= project.mapped("message_ids.attachment_ids")
            field_name = [
                "process_ids",
                "process_ids.step_ids",
                "process_ids.test_ids",
                "process_ids.development_ids",
                "process_ids.step_ids.development_ids",
                "process_ids.test_ids.test_step_ids",
                "process_ids.test_ids.test_step_ids.issue_ids",
            ]
            for field in field_name:
                if "attachment_ids" in project.mapped(field):
                    attachments |= project.mapped(field).mapped("attachment_ids")
                if "message_ids" in project.mapped(field):
                    attachments |= project.mapped(field).mapped("message_ids.attachment_ids")
            project.attachment_ids = attachments

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("code", False):
                vals["code"] = self.env["ir.sequence"].next_by_code(self._name)
        return super().create(vals)

    def _compute_display_name(self):
        for project in self:
            project.display_name = "{}{}".format(project.code and f"[{project.code}] " or "", project.name)

    def _compute_count_processes(self):
        for project in self:
            project.count_processes = len(project.process_ids)

    def _compute_count_issues(self):
        for project in self:
            project.count_issues = len(project.issue_ids)

    def _compute_count_steps(self):
        for project in self:
            project.count_steps = sum(process.count_steps for process in project.process_ids)

    def _compute_count_developments(self):
        for project in self:
            developments = self.env["business.development"].search([("project_id", "=", self.id)])
            project.count_developments = len(developments)

    def action_view_processes(self):
        domain = [("project_id", "=", self.id)]
        context = {
            "default_project_id": self.id,
            "default_customer_id": self.customer_id.id,
        }
        action = self.env["ir.actions.actions"]._for_xml_id("deltatech_business_process.action_business_process")
        action.update({"domain": domain, "context": context})
        return action

    def get_attachment_domain(self):
        domain = [
            "|",
            "|",
            "&",
            ("res_model", "=", "business.project"),
            ("res_id", "=", self.id),
            "&",
            ("res_model", "=", "business.process"),
            ("res_id", "in", self.process_ids.ids),
            "&",
            ("res_model", "=", "business.process.test"),
            ("res_id", "in", self.process_ids.test_ids.ids),
        ]
        return domain

    def _compute_attached_docs_count(self):
        for order in self:
            domain = order.get_attachment_domain()
            order.doc_count = self.env["ir.attachment"].sudo().search_count(domain)

    def attachment_tree_view(self):
        domain = self.get_attachment_domain()
        return {
            "name": _("Attachments"),
            "domain": domain,
            "res_model": "ir.attachment",
            "type": "ir.actions.act_window",
            "view_id": False,
            "view_mode": "kanban,tree,form",
            "context": f"{{'default_res_model': '{self._name}','default_res_id': {self.id}}}",
        }

    def action_view_issue(self):
        domain = [("project_id", "=", self.id)]
        context = {
            "default_project_id": self.id,
            "default_customer_id": self.customer_id.id,
        }

        action = self.env["ir.actions.actions"]._for_xml_id("deltatech_business_process.action_business_issue")
        action.update({"domain": domain, "context": context})
        return action

    def action_view_step(self):
        domain = [("process_id", "=", self.process_ids.ids)]
        context = {"default_project_id": self.id}
        action = self.env["ir.actions.actions"]._for_xml_id("deltatech_business_process.action_business_process_step")
        action.update({"domain": domain, "context": context})
        return action

    def action_view_developments(self):
        developments = self.env["business.development"].search([("project_id", "=", self.id)])
        domain = [("id", "=", developments.ids)]
        context = {"default_project_id": self.id}
        action = self.env["ir.actions.actions"]._for_xml_id("deltatech_business_process.action_business_development")
        action.update({"domain": domain, "context": context})
        return action

    def calculate_total_project_duration(self):
        for project in self:
            project.total_project_duration = sum(process.duration_for_completion for process in project.process_ids)
            for development in self.env["business.development"].search(
                [("project_id", "=", project.id), ("approved", "not in", ("draft", "rejected"))]
            ):
                project.total_project_duration += development.development_duration

    def float_to_time(self, float_hours):
        hours = int(float_hours)
        minutes = int((float_hours - hours) * 60)
        if minutes % 5 != 0:
            minutes = round(minutes / 5) * 5
        if minutes < 10:
            minutes = f"0{minutes}"
        if hours < 10:
            hours = f"0{hours}"
        return f"{hours}:{minutes}"

    def generate_excel_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        worksheet = workbook.add_worksheet()
        header_format = workbook.add_format({"bg_color": "#D0F0C0", "bold": True})
        red_text_format = workbook.add_format({"font_color": "red"})

        # Add headers
        headers = [
            "Code",
            "Name",
            "Configuration Duration",
            "Training duration",
            "Testing duration",
            "Data Migration Duration",
            "Total Duration",
        ]
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_format)
            worksheet.set_column(col_num, col_num, len(header) + 2)

        area_processes = {}
        for process in self.process_ids:
            if process.area_id:
                if process.area_id not in area_processes:
                    area_processes[process.area_id] = []
                area_processes[process.area_id].append(process)
        area_format = workbook.add_format({"bg_color": "#FFFF99", "bold": True, "align": "center"})

        row = 1
        configuration_duration = 0
        instructing_duration = 0
        data_migration_duration = 0
        duration_for_completion = 0
        duration_for_testing = 0
        for area in sorted(area_processes.keys(), key=lambda a: a.name):
            processes = area_processes[area]
            processes.sort(key=lambda p: p.code)
            worksheet.merge_range(row, 0, row, 6, f"{area.name} - {len(processes)}", area_format)
            row += 1
            for process in processes:
                format_to_use = red_text_format if process.duration_for_completion == 0 else None
                worksheet.write(row, 0, process.code, format_to_use)
                worksheet.write(row, 1, process.name, format_to_use)
                worksheet.write(row, 2, self.float_to_time(process.configuration_duration), format_to_use)
                configuration_duration += process.configuration_duration
                worksheet.write(row, 3, self.float_to_time(process.instructing_duration), format_to_use)
                instructing_duration += process.instructing_duration
                worksheet.write(row, 4, self.float_to_time(process.data_migration_duration), format_to_use)
                data_migration_duration += process.data_migration_duration
                worksheet.write(row, 5, self.float_to_time(process.testing_duration), format_to_use)
                duration_for_testing += process.testing_duration
                worksheet.write(row, 6, self.float_to_time(process.duration_for_completion), format_to_use)
                duration_for_completion += process.duration_for_completion
                row += 1
        worksheet.write(row, 1, "Total", header_format)
        worksheet.write(row, 2, self.float_to_time(configuration_duration), header_format)
        worksheet.write(row, 3, self.float_to_time(instructing_duration), header_format)
        worksheet.write(row, 4, self.float_to_time(data_migration_duration), header_format)
        worksheet.write(row, 5, self.float_to_time(duration_for_testing), header_format)
        worksheet.write(row, 6, self.float_to_time(duration_for_completion), header_format)
        # for project in self:
        #     worksheet.write(row, 0, project.code)
        #     worksheet.write(row, 1, project.name)
        #     worksheet.write(row, 2, project.customer_id.name)
        #     worksheet.write(row, 3, project.state)
        #     worksheet.write(row, 4, project.date_start and project.date_start.strftime('%Y-%m-%d') or '')
        #     worksheet.write(row, 5, project.date_go_live and project.date_go_live.strftime('%Y-%m-%d') or '')
        #     row += 1
        # worksheet.autofit()

        workbook.close()
        output.seek(0)
        return output.read()

    def action_download_excel_report(self):
        active_id = self.env.context.get("active_id")
        if not active_id:
            raise UserError(_("No active project found."))

        project = self.browse(active_id)
        excel_data = project.generate_excel_report()

        attachment = self.env["ir.attachment"].create(
            {
                "name": "Project_Report.xlsx",
                "type": "binary",
                "datas": base64.b64encode(excel_data),
                "store_fname": "Project_Report.xlsx",
                "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            }
        )

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "self",
        }
