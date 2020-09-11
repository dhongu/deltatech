# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ServiceAgreement(models.Model):
    _inherit = "service.agreement"

    group_id = fields.Many2one("service.agreement.group", string="Building")


class ServiceAgreementLine(models.Model):
    _inherit = "service.agreement.line"

    equipment_id = fields.Many2one("service.equipment", string="Apartment", index=True)


class ServiceConsumption(models.Model):
    _inherit = "service.consumption"

    equipment_id = fields.Many2one("service.equipment", string="Apartment", index=True)
    group_id = fields.Many2one("service.agreement.group", string="Building")


class ServiceAgreementGroup(models.Model):
    _name = "service.agreement.group"
    _description = "Building"

    name = fields.Char(string="Building")
