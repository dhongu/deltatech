# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import time

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Partner(models.Model):
    _inherit = "res.partner"

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if "parent_partner_id" in self.env.context:
            defaults["parent_id"] = self.env.context["parent_partner_id"]
        return defaults

    # @api.model
    # def _fields_view_get(self, view_id=None, view_type="form", toolbar=False, submenu=False):
    #     if (not view_id) and (view_type == "form") and self._context.get("simple_form"):
    #         view_id = self.env.ref("base.view_partner_simple_form").id
    #     res = super(Partner, self)._fields_view_get(
    #         view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
    #     )
    #
    #     return res

    @api.constrains("cnp")
    def check_cnp(self):
        # la import in fisiere sa nu mai faca validarea
        if "install_mode" in self.env.context:
            return True
        res = True
        for contact in self:
            res = res and self.check_single_cnp(contact.cnp)
        if not res:
            raise ValidationError(_("CNP invalid"))

    def _get_cnp_checksum(self, cnp):
        key = "279146358279"
        suma = 0
        for i in range(len(key)):
            suma += int(cnp[i]) * int(key[i])
        if suma % 11 == 10:
            rest = 1
        else:
            rest = suma % 11
        return rest

    @api.model
    def check_single_cnp(self, cnp):
        if not cnp or not cnp.strip():
            return True
        cnp = cnp.strip()
        if len(cnp) != 13:
            return False

        rest = self._get_cnp_checksum(cnp)

        ok = rest == int(cnp[12])
        return ok

    @api.onchange("cnp")
    def cnp_change(self):
        if self.cnp and len(self.cnp) > 7:
            birthdate = self.cnp[1:7]
            if self.cnp[0] in ["1", "2"]:
                birthdate = "19" + birthdate
            else:
                birthdate = "20" + birthdate
            self.birthdate = time.strftime("%Y-%m-%d", time.strptime(birthdate, "%Y%m%d"))
            if self.cnp[0] in ["1", "5"]:
                self.gender = "male"
            else:
                self.gender = "female"

    @api.onchange("birthdate")
    def birthdate_change(self):
        if self.cnp and self.birthdate:
            cnp = self.cnp
            cnp = cnp[0] + self.birthdate.strftime("%y%m%d") + cnp[7:12]

            rest = self._get_cnp_checksum(cnp)

            self.cnp = cnp + str(rest)

    cnp = fields.Char(string="CNP", size=13)

    id_series = fields.Char(string="ID series", size=2)
    id_nr = fields.Char(string="ID Nr", size=12)
    id_issued_by = fields.Char(string="ID Issued by", size=20)
    id_issued_at = fields.Date(string="ID Issued at")
    mean_transp = fields.Char(string="Mean Transport", size=12)
    is_department = fields.Boolean(string="Is Department")  # backport from v14
    birthdate = fields.Date(string="Birthdate")

    gender = fields.Selection([("male", "Male"), ("female", "Female"), ("other", "Other")])

    # nu se mai afiseaza compania la contacte
    def _get_contact_name(self, partner, name):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        contact_get_name = get_param("contact.get_name_only", default=False)
        if partner.type == "contact" and contact_get_name:
            return name
        else:
            return super()._get_contact_name(partner, name)

    def _get_name(self):
        partner = self
        context = self.env.context
        name = super()._get_name()

        if context.get("show_phone", False):
            if partner.phone or partner.mobile:
                name = f"{name}\n<{partner.phone or partner.mobile}>"
        if context.get("show_category") and partner.category_id:
            cat = []
            for category in partner.category_id:
                cat.append(category.name)
            name = name + "\n[" + ",".join(cat) + "]"
        if context.get("address_inline"):
            name = name.replace("\n", ", ")
        return name

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        res_vat = []
        if name and len(name) > 2:
            partner_ids = self.search([("vat", "ilike", name), ("is_company", "=", True)], limit=10)
            if partner_ids:
                res_vat = partner_ids.name_get()
        res = super().name_search(name, args, operator=operator, limit=limit) + res_vat
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if "cnp" in values:
                if not self.check_single_cnp(values["cnp"]):
                    values["cnp"] = ""
        return super().create(vals_list)
