# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

import re

from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import html2plaintext, is_html_empty

from .mail_signature_render import find_invalid, render

ATTACHMENT_URL = re.compile(r"/web/(?:image|content)/(\d+)(?=[/?\-\"'\s>])", re.I)
DATA_IMAGE = re.compile(r"<img[^>]+src=[\"']?data:", re.I)
HAS_SCHEME = re.compile(r"^[a-z][a-z0-9+.\-]*:(?!\d)", re.I)
MAX_IMAGES = 5
MAX_IMAGE_SIZE = 300 * 1024
IMAGE_TYPES = ("image/png", "image/jpeg", "image/gif")


class MailSignatureTemplate(models.Model):
    _name = "mail.signature.template"
    _description = "Mail Signature Template"
    _check_company_auto = True
    _order = "company_id, name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", string="Company", required=True, default=lambda self: self.env.company, index=True
    )
    auto_refresh = fields.Boolean(
        string="Refresh automatically",
        default=True,
        help="When the name, e-mail, phone, job position or mobile phone of a user changes, the "
        "signature generated for them is generated again. Hand-written signatures are never touched.",
    )
    body_html = fields.Html(
        string="Signature",
        required=True,
        # xss-ok: tag-uri sanitizate; lxml scoate on* și javascript:, atributele rămân pentru stilul semnăturii
        sanitize_attributes=False,
        sanitize_style=False,
        help="Write the signature as you want it to look. Write {{name}}, {{phone}}, ... where the data "
        "of the user or of the company must appear. A line whose fields are all empty is not shown.",
    )
    fields_help = fields.Text(string="Available fields", compute="_compute_fields_help")

    @api.model
    def _get_fields_catalog(self):
        """``{name: description}`` of the fields a template can use."""
        return {
            "name": self.env._("Name of the user"),
            "job_title": self.env._("Job position of the user"),
            "email": self.env._("E-mail of the user"),
            "phone": self.env._("Phone of the user"),
            "mobile": self.env._("Mobile phone of the user (needs the HR app)"),
            "company": self.env._("Name of the company"),
            "company_website": self.env._("Website of the company"),
            "company_phone": self.env._("Phone of the company"),
            "company_email": self.env._("E-mail of the company"),
            "company_address": self.env._("Address of the company, on one line"),
            "company_vat": self.env._("Tax ID of the company"),
        }

    def _compute_fields_help(self):
        catalog = self._get_fields_catalog()
        text = "\n".join(f"{{{{{name}}}}} - {label}" for name, label in catalog.items())
        for template in self:
            template.fields_help = text

    # --- constraints -------------------------------------------------------------------------

    @api.constrains("body_html")
    def _check_body_fields(self):
        valid = self._get_fields_catalog()
        for template in self:
            unknown, malformed = find_invalid(str(template.body_html or ""), valid)
            if unknown or malformed:
                raise ValidationError(
                    self.env._(
                        "The signature uses fields that do not exist: %(unknown)s. Valid fields: %(valid)s.",
                        unknown=", ".join(f"{{{{{n}}}}}" for n in unknown) or "{{ }}",
                        valid=", ".join(f"{{{{{n}}}}}" for n in valid),
                    )
                )

    @api.constrains("active", "company_id")
    def _check_one_active_per_company(self):
        for template in self.filtered("active"):
            other = self.search(
                [("company_id", "=", template.company_id.id), ("active", "=", True), ("id", "!=", template.id)],
                limit=1,
            )
            if other:
                raise ValidationError(
                    self.env._(
                        "The company %(company)s already has an active signature template: %(name)s.",
                        company=template.company_id.display_name,
                        name=other.name,
                    )
                )

    # --- images --------------------------------------------------------------------------------

    def _prepare_images(self):
        """Images of the body are files of Odoo that anybody can read (the recipient of a message, the
        mail client), few and small; those uploaded with the editor become public files of the template."""
        Attachment = self.env["ir.attachment"]
        for template in self:
            body = str(template.body_html or "")
            if DATA_IMAGE.search(body):
                raise ValidationError(self.env._("Add the images with the editor (upload them), not pasted as data."))
            ids = list(dict.fromkeys(int(i) for i in ATTACHMENT_URL.findall(body)))
            if not ids:
                continue
            if len(ids) > MAX_IMAGES:
                raise ValidationError(self.env._("The signature can have at most %s images.", MAX_IMAGES))
            for attachment in Attachment.browse(ids).exists():
                if attachment.mimetype not in IMAGE_TYPES:
                    raise ValidationError(self.env._("The images of the signature can only be PNG, JPEG or GIF."))
                if attachment.file_size > MAX_IMAGE_SIZE:
                    raise ValidationError(
                        self.env._("An image of the signature is larger than %s KB.", MAX_IMAGE_SIZE // 1024)
                    )
                loose = attachment.res_model in (False, self._name) and not (
                    attachment.res_id and attachment.res_id != template.id
                )
                if loose and not (attachment.public and attachment.res_id == template.id):
                    attachment.sudo().write({"public": True, "res_model": self._name, "res_id": template.id})
                elif not attachment.public:
                    raise ValidationError(
                        self.env._("An image of the signature is not shared. Upload it again with the editor.")
                    )

    @api.model_create_multi
    def create(self, vals_list):
        templates = super().create(vals_list)
        templates._prepare_images()
        return templates

    def write(self, vals):
        result = super().write(vals)
        if "body_html" in vals:
            self._prepare_images()
        return result

    # --- values and rendering ------------------------------------------------------------------

    @api.model
    def _values_of(self, user):
        """``{field: text}`` for ``user`` and the company of the user."""
        user = user.sudo()
        partner = user.partner_id
        company = user.company_id
        address = company.partner_id._display_address(without_company=True) if company.partner_id else ""
        mobile = user["mobile_phone"] if "mobile_phone" in user._fields else ""
        return {
            "name": user.name or "",
            "job_title": partner.function or "",
            "email": user.email or "",
            "phone": partner.phone or "",
            "mobile": mobile or "",
            "company": company.name or "",
            "company_website": company.website or "",
            "company_phone": company.phone or "",
            "company_email": company.email or "",
            "company_address": ", ".join(part.strip() for part in (address or "").splitlines() if part.strip()),
            "company_vat": company.vat or "",
        }

    def _render_for(self, user):
        """The signature of ``user`` from this template, as safe HTML."""
        self.ensure_one()
        values = self._values_of(user)
        href_values = dict(values)
        website = values["company_website"].strip()
        if website and not HAS_SCHEME.match(re.sub(r"[\x00-\x20]", "", website)):
            href_values["company_website"] = "https://" + website
        body = render(str(self.sudo().body_html or ""), values, href_values)
        return Markup(body)

    @api.model
    def _active_for_company(self, company):
        return self.sudo().search([("company_id", "=", company.id), ("active", "=", True)], limit=1)

    # --- actions -------------------------------------------------------------------------------

    def action_generate_signatures(self):
        """Generate the signature of the internal users of the company that have no hand-written one."""
        self.ensure_one()
        if not self.env.user.has_group("base.group_system"):
            raise UserError(self.env._("Only administrators can generate the signatures of the users."))
        if is_html_empty(self.body_html):
            raise UserError(self.env._("The template is empty."))
        users = (
            self.env["res.users"]
            .sudo()
            .search([("company_id", "=", self.company_id.id), ("share", "=", False), ("active", "=", True)])
        )
        done = skipped = 0
        for user in users:
            if user.mail_signature_generated or self._is_default_signature(user):
                user._write_generated_signature(self._render_for(user))
                done += 1
            else:
                skipped += 1
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("Signatures generated"),
                "message": self.env._(
                    "%(done)s generated, %(skipped)s with a hand-written signature left as they are.",
                    done=done,
                    skipped=skipped,
                ),
                "type": "success" if not skipped else "warning",
                "sticky": False,
            },
        }

    @api.model
    def _is_default_signature(self, user):
        """Empty, or only the name of the user (what Odoo puts for a new user): not hand-written."""
        signature = user.signature
        if is_html_empty(signature):
            return True
        text = html2plaintext(str(signature)).strip()
        return text == (user.name or "").strip() and "<img" not in str(signature)
