# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.http import request

from odoo.addons.website_helpdesk.controllers import main


class WebsiteHelpdesk(main.WebsiteHelpdesk):
    def get_helpdesk_team_data(self, team, search=None):
        result = super(WebsiteHelpdesk, self).get_helpdesk_team_data(team, search)
        partner = request.env.user.partner_id
        result["partner_email"] = partner.email
        result["partner_name"] = partner.name
        return result
