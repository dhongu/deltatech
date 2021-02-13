# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


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

    def get_readings(self):
        readings = self.env["service.meter.reading"].search([("equipment_history_id", "=", self.id)], order="date")
        return readings


class ServiceEquipment(models.Model):
    _inherit = "service.equipment"

    equipment_history_id = fields.Many2one("service.equipment.history", string="Equipment actual location", copy=False)

    equipment_history_ids = fields.One2many("service.equipment.history", "equipment_id", string="Equipment History")

    common_history_ids = fields.One2many("common.history", "equipment_id", string="Equipment History")

    def common_history_button(self):
        common_histories = self.common_history_ids
        # context = {
        #     'default_equipment_id': self.id,
        #     'default_partner_id': self.partner_id.id,
        #     'default_agreement_id': self.agreement_id.id,
        #     'default_address_id': self.address_id.id,
        #     'default_contact_id': self.contact_id.id,
        # }
        return {
            "domain": "[('id','in', [" + ",".join(map(str, common_histories.ids)) + "])]",
            "name": "Istoric",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "common.history",
            "view_id": False,
            # 'context': context,
            "type": "ir.actions.act_window",
        }

    def remove_from_agreement_button(self):
        counters = ""
        if self.meter_ids:
            for meter in self.meter_ids:
                counters += str(meter.uom_id.name) + ": " + str(meter.total_counter_value) + "\r\n"
        emplacement = self.emplacement or ""
        values = {
            "name": "Scoatere din contract",
            "equipment_id": self.id,
            "agreement_id": self.agreement_id.id,
            # 'description': 'Scoatere din contract.\r\nlContori:' + counters
            "description": "Scoatere din contract nr "
            + str(self.agreement_id.name)
            + ", Partener "
            + str(self.partner_id.name)
            + ", punct de lucru "
            + str(self.address_id.name)
            + ", amplasament "
            + emplacement
            + ".\r\nContori:"
            + counters,
        }
        self.env["common.history"].create(values)
        return super(ServiceEquipment, self).remove_from_agreement_button()
