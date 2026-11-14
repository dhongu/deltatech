# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    llms_txt_enabled = fields.Boolean(related="website_id.llms_txt_enabled", readonly=False)
    llms_txt_url = fields.Char(related="website_id.llms_txt_url")

    def action_open_llms_txt(self):
        """The texts of llms.txt are long Markdown: they are written on the website form, full width."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("llms.txt"),
            "res_model": "website",
            "res_id": self.website_id.id,
            "views": [(self.env.ref("website.view_website_form").id, "form")],
            "target": "current",
        }
