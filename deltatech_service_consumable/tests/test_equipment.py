# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tools.safe_eval import safe_eval

from odoo.addons.deltatech_service_agreement.tests.test_agreement import TestAgreement
from odoo.addons.deltatech_service_equipment_base.tests.test_service import TestService


class TestAgreementEquipment(TestAgreement, TestService):
    def setUp(self):
        super().setUp()
        self.get_param = self.env["ir.config_parameter"].sudo().get_param
        picking_type_for_service = self.get_param("service.picking_type_for_service")
        if not picking_type_for_service:
            picking_type_for_service = self.env["stock.picking.type"].create(
                {
                    "name": "Test Picking Type",
                    "code": "outgoing",
                    "sequence_code": "TEST",
                }
            )
            self.env["ir.config_parameter"].sudo().set_param(
                "service.picking_type_for_service", picking_type_for_service.id
            )

        self.consumable_item = self.env["service.consumable.item"].create(
            {
                "type_id": self.equipment_type.id,
                "product_id": self.product_1.id,
            }
        )

        self.equipment = self.env["service.equipment"].create(
            {
                "name": "Test Equipment",
                "type_id": self.equipment_type.id,
                "model_id": self.equipment_model.id,
            }
        )
        self.meter = self.env["service.meter"].create(
            {
                "name": "Test Meter",
                "meter_categ_id": self.meter_category.id,
                "equipment_id": self.equipment.id,
                "uom_id": self.env.ref("uom.product_uom_unit").id,
            }
        )

    def test_equipment(self):
        self.quantity = self.consumable_item.with_context(equipment_id=self.equipment.id).quantity
        self.equipment.new_piking_button()
        consumables = self.equipment.consumable_item_ids
        self.assertEqual(len(consumables), 1)

        self.equipment.delivered_button()
        self.equipment.picking_button()

    def test_agreement(self):
        agreement = Form(self.env["service.agreement"])
        agreement.name = "Test Agreement"
        agreement.partner_id = self.partner_1
        agreement.type_id = self.agreement_type
        agreement.cycle_id = self.cycle

        with agreement.agreement_line.new() as agreement_line:
            agreement_line.product_id = self.product_1
            agreement_line.quantity = 1
            agreement_line.price_unit = 100
            agreement_line.equipment_id = self.equipment
            agreement_line.meter_id = self.meter

        agreement = agreement.save()
        agreement.contract_open()

        agreement.picking_button()
        agreement.compute_costs()
        agreement.compute_percent()

    def test_picking(self):
        picking_type_id = safe_eval(self.get_param("service.picking_type_for_service", "False"))

        picking_type_for_service = self.env["stock.picking.type"].browse(picking_type_id)

        picking = Form(self.env["stock.picking"])
        picking.partner_id = self.partner_1
        picking.picking_type_id = picking_type_for_service
        picking.equipment_id = self.equipment
        with picking.move_ids_without_package.new() as move:
            move.product_id = self.product_1
            move.product_uom_qty = 1
            # move.product_uom_id = self.product_1.uom_id

        picking = picking.save()
        picking.check_consumable()
        picking.action_assign()

        self.env["service.efficiency.report"].get_usage(
            "2000-01-01",
            "2999-12-31",
            self.equipment.id,
            self.product_1.uom_id.id,
            self.product_1.id,
        )
