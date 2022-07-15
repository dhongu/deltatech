# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models


class DeltatechDC(models.Model):
    _name = "deltatech.dc"
    _description = "Declaration of Conformity"

    name = fields.Char("Number", size=32, required=True)
    date = fields.Date("Date of Declaration", required=True, index=True)
    product_id = fields.Many2one(
        "product.product", "Product", required=True, index=True, domain=[("sale_ok", "=", "True")]
    )
    company_standard = fields.Char(related="product_id.company_standard", string="Standard of Company", store=False)
    data_sheet = fields.Integer(related="product_id.data_sheet", string="Data Sheet", store=False)
    technical_specification = fields.Integer(
        related="product_id.technical_specification", string="Technical Specification", store=False
    )
    standards = fields.Text(related="product_id.standards", string="Standards", store=False)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)

    def name_get(self):
        result = []
        for line in self:
            name = (line.product_id.name or "") + " (" + (line.name or "") + "/" + (str(line.date) or "") + ")"
            result.append((line.id, name))

        return result

    @api.model
    def create(self, vals):
        if "company_id" in vals:
            self = self.with_company(vals["company_id"])
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code("declaration.conformity") or _("New")

        result = super(DeltatechDC, self).create(vals)
        return result
