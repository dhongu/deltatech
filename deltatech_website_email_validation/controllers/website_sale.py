# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleEmailValidation(WebsiteSale):
    def checkout_form_validate(self, mode, all_form_values, data):

        error = dict()
        error_message = []

        standard_error, standard_error_message = super(WebsiteSaleEmailValidation, self).checkout_form_validate(
            mode, all_form_values, data
        )

        error.update(standard_error)
        error_message += standard_error_message

        if data.get("email") and mode[0] == "new" and "email" not in error:
            Partner = request.env["res.partner"].sudo()
            Users = request.env["res.users"].sudo()
            partners = Partner.search([("email", "=", data.get("email"))])
            if partners:
                users = Users.search([("partner_id", "in", partners.ids)])
                if users:
                    error["email"] = "error"
                    error_message.append(_("There is a client in the system with this email address"))

        return error, error_message

    def _checkout_form_save(self, mode, checkout, all_values):
        if mode[0] == "new":
            checkout["active"] = False
        partner_id = super(WebsiteSaleEmailValidation, self)._checkout_form_save(mode, checkout, all_values)

        return partner_id
