# © 2026 Deltatech
# See README.rst file on addons root folder for license details
from urllib.parse import quote

from odoo import fields, models

IMG_PATH = "/deltatech_website_legal_guarantee/static/src/img/notice/"

# Fișierele oficiale ale Comisiei Europene (Regulamentul de punere în aplicare (UE) 2025/1960,
# anexa I), nemodificate, în cele 24 de limbi oficiale ale UE: PNG color pentru afișare și PDF pentru
# descărcare. Comisia nu publică PNG în engleză, doar SVG.
NOTICE_LANGS = (
    "bg", "cs", "da", "de", "el", "en", "es", "et", "fi", "fr", "ga", "hr",
    "hu", "it", "lt", "lv", "mt", "nl", "pl", "pt", "ro", "sk", "sl", "sv",
)  # fmt: skip
NOTICE_IMAGE_EXT = {"en": "svg"}

# Destinația codului QR din notificare, pe limbi (ghidul DG JUST, aprilie 2026, cap. 2.3)
YOUREUROPE_PATHS = {
    "bg": "гаранции",
    "cs": "záruky_cs",
    "da": "garantier",
    "de": "garantien",
    "el": "εγγυήσεις",
    "en": "guarantees",
    "es": "garantías",
    "et": "garantiid",
    "fi": "virhevastuu",
    "fr": "garanties",
    "ga": "ráthaíochtaí",
    "hr": "jamstva_hr",
    "hu": "jótállás",
    "it": "garanzie",
    "lt": "garantijos",
    "lv": "garantijas",
    "mt": "garanziji",
    "nl": "garantie",
    "pl": "gwarancje",
    "pt": "garantias",
    "ro": "garanții",
    "sk": "záruky_sk",
    "sl": "jamstva_sl",
    "sv": "reklamationsrätt",
}


class Website(models.Model):
    _inherit = "website"

    legal_guarantee_footer = fields.Boolean("Legal guarantee link in footer", default=True)
    legal_guarantee_product = fields.Boolean("Legal guarantee on product page", default=True)
    legal_guarantee_checkout = fields.Boolean("Legal guarantee at checkout", default=True)

    def _get_legal_guarantee_notice(self):
        """Notificarea armonizată UE în limba curentă; engleza pentru o limbă din afara celor 24 ale UE."""
        lang = (self.env.lang or "en_US").split("_")[0]
        if lang not in NOTICE_LANGS:
            lang = "en"
        link_text = "europa.eu/youreurope/" + YOUREUROPE_PATHS[lang]
        return {
            "image_url": f"{IMG_PATH}legal_guarantee_notice_{lang}.{NOTICE_IMAGE_EXT.get(lang, 'png')}",
            "pdf_url": f"{IMG_PATH}legal_guarantee_notice_{lang}.pdf",
            "link_text": link_text,
            "link_url": "https://" + quote(link_text),
        }

    def _get_legal_guarantee_national_template(self):
        """Șablonul QWeb cu partea națională (drepturi, autorități) a țării companiei website-ului.

        Un modul de țară adaugă șablonul ``deltatech_website_legal_guarantee.national_<cod țară>``;
        fără el, pagina arată doar textul generic după Directiva (UE) 2019/771.
        """
        self.ensure_one()
        code = (self.company_id.country_id.code or "").lower()
        template = f"deltatech_website_legal_guarantee.national_{code}"
        if code and self.env["ir.ui.view"].sudo().search_count([("key", "=", template)]):
            return template
        return False

    def _get_legal_guarantee_seller(self):
        """Datele vânzătorului: compania website-ului, fără numele repetat în adresă și fără linii goale."""
        self.ensure_one()
        company = self.company_id
        address = company.partner_id._display_address(without_name=True)
        return {
            "name": company.name,
            "vat": company.vat,
            "address": "\n".join(line.strip() for line in (address or "").splitlines() if line.strip()),
            "phone": company.phone,
            "email": company.email,
        }
