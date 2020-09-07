# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.http import request


class website(models.Model):
    _inherit = "website"

    def sale_product_domain(self):
        domain = super(website, self).sale_product_domain()
        search = request.params.get("search", False)
        if search:
            if self.env.user.share:
                values = {"user_id": self.env.user.id, "date": fields.Datetime.now(), "word": search}
                self.env["website.user.search"].sudo().create(values)

        return domain
