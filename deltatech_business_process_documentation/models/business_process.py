# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class BusinessProcess(models.Model):
    _inherit = "business.process"

    slide_id = fields.Many2one(string="Slide", comodel_name="slide.slide")
    website_published = fields.Boolean(related="slide_id.website_published", store=True)

    def write(self, vals):
        result = super().write(vals)
        self.generate_documentation()
        return result

    def generate_documentation(self):
        for process in self:
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
            "slide_type": "webpage",
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

    # def generate_documentation_from_steps_old(self):
    #     for process in self:
    #         table_of_content = process.generate_table_of_content()
    #         steps_content = process.generate_steps_content()
    #
    #         html_content = """
    # <section class="s_table_of_content pt24 pb24 o_cc o_cc1 o_colored_level"
    #         data-snippet="s_table_of_content" data-name="Table of Content"
    #         style="background-image: none;">
    #     <div class="container">
    #         <div class="row s_nb_column_fixed">
    #             {}
    #             {}
    #         </div>
    #     </div>
    # </section>
    #     """.format(
    #             table_of_content,
    #             steps_content,
    #         )
    #         process.slide_id.html_content = html_content
    #
    # def generate_table_of_content(self):
    #     table_of_content = """
    # <div class="col-lg-3 s_table_of_content_navbar_wrap s_table_of_content_navbar_sticky
    #         s_table_of_content_vertical_navbar d-print-none d-none d-lg-block o_not_editable
    #         o_cc o_cc1 o_colored_level" data-name="Navbar">
    #     <div class="s_table_of_content_navbar list-group o_no_link_popover" style="">
    #     """
    #     for step in self.step_ids:
    #         table_of_content += """
    #             <a href="#table_of_content_heading_{}"
    #                 class="table_of_content_link list-group-item list-group-item-action
    #                 py-2 border-0 rounded-0 active">{}</a>
    #         """.format(
    #             step.id,
    #             step.name,
    #         )
    #     table_of_content += """
    #     </div>
    # </div>
    #     """
    #     return table_of_content
    #
    # def generate_steps_content(self):
    #     steps_content = """
    # <div class="col-lg-9 s_table_of_content_main oe_structure oe_empty o_colored_level" data-name="Content">
    #     """
    #     if self.description:
    #         steps_content += (
    #             """
    #         <section class="pb16 o_colored_level" style="background-image: none;">
    #             <h1 data-anchor="true" class="o_default_snippet_text">Description</h1>
    #             %s
    #             <h1 data-anchor="true" class="o_default_snippet_text">Steps</h1>
    #         </section>
    #         """
    #             % self.description
    #         )
    #     for step in self.step_ids:
    #         steps_content += """
    #         <section class="pb16 o_colored_level" style="background-image: none;">
    #             <h1 data-anchor="true" class="o_default_snippet_text" id="table_of_content_heading_{}">{}</h1>
    #             {}
    #         </section>
    #         """.format(
    #             step.id,
    #             step.name,
    #             step.details,
    #         )
    #     steps_content += """
    # </div>
    #     """
    #     return steps_content
