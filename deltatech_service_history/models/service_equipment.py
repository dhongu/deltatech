# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class ServiceEquipmentHistory(models.Model):
    _name = "service.equipment.history"
    _description = "Equipment History"
    _order = "equipment_id, from_date DESC"

    name = fields.Char(string="Name", related="equipment_id.name")
    from_date = fields.Date(string="Installation Date", required=True, index=True)

    equipment_id = fields.Many2one("service.equipment", string="Equipment", ondelete="cascade", index=True)

    # cind se actulizeaza  agreement_id?
    agreement_id = fields.Many2one("service.agreement", string="Service Agreement")
    partner_id = fields.Many2one("res.partner", string="Customer", help="The customer where the equipment is installed")
    address_id = fields.Many2one(
        "res.partner", string="Location", help="The working point where the equipment was located"
    )
    emplacement = fields.Char(string="Emplacement", help="Detail of location of the equipment in working point")

    equipment_backup_id = fields.Many2one("service.equipment", string="Backup Equipment")

    active = fields.Boolean(default=True)

    # dupa ce se introduce un nou contor se verifica daca are citiri introduse la data din istoric echipament
    # la instalare dezinstalare se citesc automat contorii si se genereaza consumuri !! planificat???
    @api.multi
    def get_readings(self):
        readings = self.env["service.meter.reading"].search([("equipment_history_id", "=", self.id)], order="date")
        return readings


class ServiceEquipment(models.Model):
    _inherit = "service.equipment"

    equipment_history_id = fields.Many2one("service.equipment.history", string="Equipment actual location", copy=False)

    equipment_history_ids = fields.One2many("service.equipment.history", "equipment_id", string="Equipment History")
