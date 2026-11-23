# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.exceptions import AccessError, UserError

from .res_partner import REFRESH_FIELDS


class ResUsers(models.Model):
    _inherit = "res.users"

    mail_signature_generated = fields.Boolean(
        string="Signature from the company template",
        readonly=True,
        copy=False,
        help="The signature was generated from the signature template of the company. Editing it by hand "
        "clears this mark; a signature without it is never overwritten by a mass generation.",
    )

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ["mail_signature_generated"]

    def write(self, vals):
        result = super().write(vals)
        if "signature" in vals and not self.env.context.get("mail_signature_generating"):
            self.sudo().filtered("mail_signature_generated").write({"mail_signature_generated": False})
        elif REFRESH_FIELDS & set(vals) and "signature" not in vals:
            self.sudo()._refresh_generated_signature()
        return result

    def _write_generated_signature(self, html):
        self.sudo().with_context(mail_signature_generating=True).write(
            {"signature": html, "mail_signature_generated": True}
        )

    def _refresh_generated_signature(self):
        """Generate again the signature of the users that have a generated one."""
        if self.env.context.get("mail_signature_generating"):
            return
        Template = self.env["mail.signature.template"]
        for user in self.filtered(lambda u: u.mail_signature_generated and u.active and not u.share):
            template = Template._active_for_company(user.company_id)
            if template and template.auto_refresh:
                user._write_generated_signature(template._render_for(user))

    def action_regenerate_signature(self):
        """Replace the signature of the user by the one of the template of their company."""
        self.ensure_one()
        if self != self.env.user and not self.env.user.has_group("base.group_system"):
            raise AccessError(self.env._("You can only regenerate your own signature."))
        template = self.env["mail.signature.template"]._active_for_company(self.sudo().company_id)
        if not template:
            raise UserError(
                self.env._(
                    "The company %s has no active signature template.",
                    self.sudo().company_id.display_name,
                )
            )
        self._write_generated_signature(template._render_for(self))
        return {"type": "ir.actions.client", "tag": "reload"}
