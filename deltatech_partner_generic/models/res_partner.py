# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models, tools
from odoo.exceptions import UserError

EDITOR_GROUP = "deltatech_partner_generic.group_generic_partner_editor"

# Fields written by standard Odoo flows (chatter, activities, portal signup,
# GeoIP, website) that must keep working on a protected partner.
TECHNICAL_FIELDS = frozenset(
    {
        "activity_ids",
        "date_localization",
        "generic_partner_locked",
        "last_website_so_id",
        "message_bounce",
        "message_follower_ids",
        "message_ids",
        "message_main_attachment_id",
        "message_partner_ids",
        "partner_gid",
        "signup_expiration",
        "signup_token",
        "signup_type",
    }
)


class ResPartner(models.Model):
    _inherit = "res.partner"

    generic_partner_locked = fields.Boolean(
        string="Generic Partner Protected",
        compute="_compute_generic_partner_locked",
        help="Technical field: this partner is the generic partner of a company "
        "that protects it, and the current user is not allowed to modify it.",
    )

    @api.model
    @tools.ormcache()
    def _get_protected_generic_partner_ids(self):
        """Ids of the generic partners of the companies that ask for protection.

        Cached: this runs on every write() on any partner, which is a hot path.
        ``res.company`` invalidates the cache when the setting changes.

        Searched in sudo on purpose: the partner must stay protected even for a
        user who has no access to the company that declared it.
        """
        companies = self.env["res.company"].sudo().search([("lock_generic_partner", "=", True)])
        return frozenset(companies.generic_partner_id.ids)

    def _generic_partners_to_protect(self):
        """Subset of ``self`` the current user is not allowed to touch."""
        protected_ids = self._get_protected_generic_partner_ids()
        # Nothing is protected on most databases: leave before touching acl.
        if not protected_ids or self.env.su:
            return self.browse()
        common = protected_ids.intersection(self.ids)
        if not common or self.env.user.has_group(EDITOR_GROUP):
            return self.browse()
        return self.browse(common)

    @api.depends_context("uid", "su")
    def _compute_generic_partner_locked(self):
        protected = self._generic_partners_to_protect()
        for partner in self:
            partner.generic_partner_locked = partner in protected

    def _raise_generic_partner_locked(self, protected):
        raise UserError(
            self.env._(
                "The generic partner “%(name)s” is protected and cannot be modified. "
                "Ask an administrator if this partner really has to be changed.",
                name=protected[0].sudo().display_name,
            )
        )

    def write(self, vals):
        protected = self._generic_partners_to_protect()
        if protected and not set(vals) <= TECHNICAL_FIELDS:
            self._raise_generic_partner_locked(protected)
        return super().write(vals)

    def unlink(self):
        protected = self._generic_partners_to_protect()
        if protected:
            self._raise_generic_partner_locked(protected)
        return super().unlink()
