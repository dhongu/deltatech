# ©  2015-2022 Deltatech
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models


class ServiceEquipment(models.Model):
    _name = "service.equipment"
    _description = "Service Equipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Reference", index=True, default=lambda self: _("New"))
    display_name = fields.Char(compute="_compute_display_name")
    partner_id = fields.Many2one("res.partner", string="Customer")
    contact_id = fields.Many2one(
        "res.partner",
        string="Contact Person",
        tracking=True,
        domain=[("type", "=", "contact"), ("is_company", "=", False)],
    )

    note = fields.Text(string="Notes")
    type_id = fields.Many2one("service.equipment.type", required=False, string="Type")
    internal_type = fields.Selection([("equipment", "Equipment")], default="equipment")
    product_id = fields.Many2one(
        "product.product", string="Product", ondelete="restrict", domain=[("type", "=", "product")]
    )

    serial_id = fields.Many2one(
        "stock.lot",
        string="Product Serial Number",
        ondelete="restrict",
        copy=False,
        domain="[('product_id','=',product_id)]",
    )
    serial_no = fields.Char("Serial Number", copy=False)

    vendor_id = fields.Many2one("res.partner", string="Vendor")
    manufacturer_id = fields.Many2one("res.partner", string="Manufacturer")
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)

    technician_user_id = fields.Many2one("res.users", string="Responsible", tracking=True)

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New") or vals.get("name") == "/":
            vals["name"] = self.env["ir.sequence"].next_by_code("service.equipment") or _("New")
        return super(ServiceEquipment, self).create(vals)

    @api.onchange("product_id")
    def onchange_product_id(self):
        if self.product_id:
            domain = [("product_id", "=", self.product_id.id)]
        else:
            domain = []
        return {"domain": {"serial_id": domain}}

    @api.onchange("serial_id")
    def onchange_serial_id(self):
        if self.serial_id:
            self.serial_no = self.serial_id.name

    def name_get(self):
        res = []
        for equipment in self:
            name = equipment.name
            if equipment.serial_id:
                name += "/" + equipment.serial_id.name
            res.append((equipment.id, name))
        return res


class ServiceEquipmentType(models.Model):
    _name = "service.equipment.type"
    _description = "Service Equipment Type"

    name = fields.Char(string="Type", translate=True)


# class ServiceEquipmentCategory(models.Model):
#     _name = "service.equipment.category"
#     _description = "Service Equipment Category"
#
#     name = fields.Char(string="Category", translate=True)
