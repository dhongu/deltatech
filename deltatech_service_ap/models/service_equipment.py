# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class ServiceEquipment(models.Model):
    _description = "Apartment"
    _inherit = "service.equipment"

    internal_type = fields.Selection(selection_add=[("apartment", "Apartment")])
    group_id = fields.Many2one("service.agreement.group", string="Building")

    @api.multi
    def _update_labels(self):
        translations = self.env["ir.translation"].search(
            [("module", "like", "service"), ("source", "like", "Equipment")]
        )
        translations.unlink()
        translations = self.env["ir.translation"].search(
            [("module", "like", "service"), ("source", "like", "Service Group")]
        )
        translations.unlink()


# class service_equipment_category(models.Model):
#     _inherit = 'service.equipment.category'
#     _description = "Apartment Category"
#     name = fields.Char(string='Category', translate=True)


class ServiceEquipmentType(models.Model):
    _inherit = "service.equipment.type"
    _description = "Apartment Type"
