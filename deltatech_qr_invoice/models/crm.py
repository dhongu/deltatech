# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class UtmCampaign(models.Model):
    _inherit = "utm.campaign"

    short_text_qr = fields.Char(string="Short text QR")
    text_qr = fields.Char(string="Text QR")
    image_qr_html = fields.Html(string="QR image", compute="_compute_image_qr_html")

    def _compute_image_qr_html(self):
        for item in self:
            item.image_qr_html = "<img src='/report/barcode/?type={}&value={}&width={}&height={}'/>".format(
                "QR",
                item.text_qr,
                100,
                100,
            )

    def show_qr(self):
        # <img t-att-src="'/report/barcode/?type=%s&amp;value=%s&amp;width=%s&amp;height=%s' %   ('QR', o.name, 200, 200)"/>
        url = "/report/barcode/?type={}&value={}&width={}&height={}".format("QR", self.text_qr, 200, 200)

        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }
