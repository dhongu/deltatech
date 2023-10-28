# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class BusinessProject(models.Model):
    _inherit = "business.project"

    auto_generate_doc = fields.Boolean(string="Auto generate documentation", default=False)
    channel_id = fields.Many2one(string="Channel", comodel_name="slide.channel")
    website_published = fields.Boolean(related="channel_id.website_published", store=True)

    def write(self, vals):
        result = super().write(vals)
        self._generate_documentation()
        return result

    def _generate_documentation(self):
        for project in self:
            if project.auto_generate_doc:
                project._generate_documentation_for_project()
            else:
                project._remove_documentation_for_project()

    def _generate_documentation_for_project(self):
        for project in self:
            if not project.channel_id:
                values = project._prepare_channel_values()
                channel = self.env["slide.channel"].create(values)
                project.channel_id = channel.id
            if project.channel_id:
                project.generate_documentation()

    def _remove_documentation_for_project(self):
        for project in self:
            if project.channel_id:
                project.channel_id.slide_ids.unlink()
                project.channel_id.unlink()

    def _prepare_channel_values(self):
        values = {
            "name": self.name,
            "channel_type": "documentation",
            "visibility": "members",
            "enroll": "invite",
            "active": True,
            "website_published": True,
        }
        return values

    def generate_documentation(self):
        for project in self:
            for process in project.process_ids:
                process.generate_documentation()
