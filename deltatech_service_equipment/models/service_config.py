# ©  2015-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models

# # se va utiliza maintenance.equipment.category
# class ServiceEquipmentCategory(models.Model):
#     _inherit = "maintenance.equipment.category"
#
#     template_meter_ids = fields.One2many("service.template.meter", "categ_id")


class ServiceEquipmentType(models.Model):
    _inherit = "service.equipment.type"

    # categ_id = fields.Many2one("maintenance.equipment.category", string="Category")

    template_meter_ids = fields.One2many("service.template.meter")

    # @api.depends("categ_id")
    # def _compute_template_meter_ids(self):
    #     for equipment_type in self:
    #         equipment_type.template_meter_ids = equipment_type.categ_id.template_meter_ids


# este utilizat pentru generare de pozitii noi in contract si pentru adugare contori noi
class ServiceTemplateMeter(models.Model):
    _inherit = "service.template.meter"

    # categ_id = fields.Many2one("maintenance.equipment.category", string="Category")

    bill_uom_id = fields.Many2one("uom.uom", string="Billing Unit of Measure")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        domain=[("name", "in", ["RON", "EUR"])],
    )
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)

    @api.onchange("meter_categ_id")
    def onchange_meter_categ_id(self):
        self.bill_uom_id = self.meter_categ_id.bill_uom_id
