# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class BusinessProcess(models.Model):
    _inherit = "business.process"

    slide_id = fields.Many2one(string="Slide", comodel_name="slide.slide", copy=False)
    website_published = fields.Boolean(related="slide_id.website_published", store=True)

    def write(self, vals):
        result = super().write(vals)
        self.generate_documentation()
        return result

    def generate_documentation(self):
        for process in self:
            if process.project_id.auto_generate_doc:
                if not process.slide_id:
                    values = process._prepare_slide_values()
                    slide = self.env["slide.slide"].create(values)
                    process.slide_id = slide.id
                if process.slide_id:
                    process.generate_documentation_from_steps()

    def _prepare_slide_values(self):
        tags = self.env["slide.tag"]
        if self.process_group_id:
            tags = self.env["slide.tag"].search([("name", "=", self.process_group_id.name)])
            if not tags:
                tags = self.env["slide.tag"].create({"name": self.process_group_id.name})
        values = {
            "name": self.name,
            "channel_id": self.project_id.channel_id.id,
            "active": True,
            "slide_category": "article",
            "website_published": True,
            "tag_ids": [(6, 0, tags.ids)],
        }
        return values

    def generate_documentation_from_steps(self):
        for process in self:
            # rendare template
            template = "deltatech_business_process_documentation.business_process_documentation"
            html_content = self.env["ir.ui.view"]._render_template(template, values={"doc": process})
            process.slide_id.html_content = html_content
