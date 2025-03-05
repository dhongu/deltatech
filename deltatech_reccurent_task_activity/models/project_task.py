from odoo import api, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        for task in tasks:
            if task.recurring_task:
                for user in task.user_ids:
                    self.env["mail.activity"].create(
                        {
                            "res_model_id": self.env.ref("project.model_project_task").id,
                            "res_id": task.id,
                            "activity_type_id": self.env.ref("mail.mail_activity_data_todo").id,
                            "summary": task.name,
                            "user_id": user.id,
                            "date_deadline": task.date_deadline,
                        }
                    )
        return tasks
