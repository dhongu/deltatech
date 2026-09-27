# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class CountryState(models.Model):
    _inherit = "res.country.state"

    city_ids = fields.One2many("res.city", "state_id")

    def get_website_sale_cities(self):
        return self.sudo().city_ids


class ResCountry(models.Model):
    _inherit = "res.country"

    def _enforce_city_choice(self):
        """Offer the city dropdown on the website for every country with `enforce_cities`.

        In 20.0 `portal` restricts the dropdown to BR, CL, PE, CO and TW; this module
        is about enabling it elsewhere (Romania with `l10n_ro_city`, first of all).
        """
        if not self:
            return False
        self.ensure_one()
        return self.enforce_cities and bool(
            self.env["res.city"].sudo().search_count([("country_id", "=", self.id)], limit=1)
        )
