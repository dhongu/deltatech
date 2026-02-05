# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        ctx = self.env.context

        # If a default pricelist is already provided via context or already set, respect it
        if defaults.get("pricelist_id") or ctx.get("default_pricelist_id"):
            return defaults

        # Try to resolve the related project to propose its pricelist in the form (before save)
        project_id = (
            ctx.get("create_for_project_id")
            or ctx.get("default_project_id")
            or ctx.get("project_id")
            or defaults.get("project_id")
        )
        # Fallback: if creating from a task, use the task's project
        if not project_id and ctx.get("create_for_task_id"):
            task = self.env["project.task"].browse(ctx["create_for_task_id"])  # sudo not required to read project_id
            if task.exists() and task.project_id:
                project_id = task.project_id.id

        if project_id:
            project = self.env["project.project"].browse(project_id)
            if project.sudo().exists() and project.pricelist_id:
                defaults["pricelist_id"] = project.pricelist_id.id

        return defaults

    @api.model_create_multi
    def create(self, vals_list):
        # Ensure the project's pricelist is used when creating a SO from a project/task
        ctx = self.env.context
        for vals in vals_list:
            if vals.get("pricelist_id"):
                continue
            # Try to resolve a related project
            project_id = ctx.get("create_for_project_id") or ctx.get("default_project_id") or vals.get("project_id")
            # Fallback: if creating from a task, use its project
            if not project_id and ctx.get("create_for_task_id"):
                task = self.env["project.task"].browse(
                    ctx["create_for_task_id"]
                )  # sudo not required to read project_id
                if task.exists() and task.project_id:
                    project_id = task.project_id.id

            if project_id:
                project = self.env["project.project"].browse(project_id)
                if project.sudo().exists() and project.pricelist_id:
                    vals["pricelist_id"] = project.pricelist_id.id
        return super().create(vals_list)
