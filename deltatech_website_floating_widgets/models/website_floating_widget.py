# © 2024 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class WebsiteFloatingWidget(models.Model):
    _name = "website.floating.widget"
    _description = "Website Floating Widget"
    _order = "sequence"

    name = fields.Char(string="Name", required=True)
    icon = fields.Selection(
        [
            ("fa-phone", "Phone"),
            ("fa-envelope", "Email"),
            ("fa-whatsapp", "WhatsApp"),
            ("fa-facebook", "Facebook"),
            ("fa-instagram", "Instagram"),
            ("fa-twitter", "Twitter"),
            ("fa-linkedin", "LinkedIn"),
            ("fa-tiktok", "TikTok"),
            ("fa-info", "Info"),
            ("fa-question", "Question"),
            ("fa-exclamation", "Exclamation"),
            ("fa-map-marker", "Map Marker"),
            ("fa-globe", "Globe"),
            ("fa-comment", "Comment"),
            ("fa-comments", "Comments"),
            ("fa-user", "User"),
            ("fa-search", "Search"),
            ("fa-external-link", "External Link"),
            ("fa-at", "At"),
            ("fa-link", "Link"),
            ("fa-share-alt", "Share"),
        ],
        string="Icon",
        required=True,
        default="fa-info",
    )
    icon_preview = fields.Html(string="Preview", compute="_compute_icon_preview")
    link = fields.Char(string="Link", required=True)
    type = fields.Selection(
        [("url", "URL"), ("phone", "Phone"), ("email", "Email")], string="Type", default="url", required=True
    )
    sequence = fields.Integer(string="Sequence", default=10)
    display_on_mobile = fields.Boolean(string="Display on Mobile", default=True)
    display_on_desktop = fields.Boolean(string="Display on Desktop", default=True)
    active = fields.Boolean(string="Active", default=True)
    background_color = fields.Char(string="Background Color", default="#875A7B")
    text_color = fields.Char(string="Text Color", default="#FFFFFF")
    button_shape = fields.Selection(
        [
            ("circle", "Circle"),
            ("square", "Square"),
            ("rounded", "Rounded"),
        ],
        string="Button Shape",
        default="circle",
        required=True,
    )

    def get_link(self):
        self.ensure_one()
        if self.type == "phone":
            return f"tel:{self.link}"
        if self.type == "email":
            return f"mailto:{self.link}"
        return self.link

    @api.depends("icon")
    def _compute_icon_preview(self):
        for record in self:
            if record.icon:
                record.icon_preview = f'<i class="fa {record.icon}" style="font-size: 24px;"></i>'
            else:
                record.icon_preview = False
