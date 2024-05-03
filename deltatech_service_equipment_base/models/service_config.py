# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ServiceMeterCategory(models.Model):
    _name = "service.meter.category"
    _description = "Service Meter Category"

    name = fields.Char(string="Category")
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure", required=True)
    type = fields.Selection(
        [("counter", "Counter"), ("collector", "Collector")],
        string="Type",
        default="counter",
    )


class ServiceEquipmentType(models.Model):
    _name = "service.equipment.type"
    _description = "Service Equipment Type"

    name = fields.Char(string="Type", translate=True)
    template_meter_ids = fields.One2many("service.template.meter", "type_id", string="Meters")


class ServiceEquipmentModel(models.Model):
    _name = "service.equipment.model"
    _description = "Service Equipment Model"

    name = fields.Char(string="Model", translate=True)


class ServiceTemplateMeter(models.Model):
    _name = "service.template.meter"
    _description = "Service Template Meter"

    type_id = fields.Many2one("service.equipment.type", string="Type")
    product_id = fields.Many2one(
        "product.product",
        string="Service",
        ondelete="set null",
        domain=[("type", "=", "service")],
    )
    meter_categ_id = fields.Many2one("service.meter.category", string="Meter category")

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
