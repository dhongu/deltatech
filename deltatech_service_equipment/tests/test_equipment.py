# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo.tests import Form

from odoo.addons.deltatech_service_agreement.tests.test_agreement import TestAgreement
from odoo.addons.deltatech_service_equipment_base.tests.test_service import TestService


class TestAgreementEquipment(TestAgreement, TestService):
    def setUp(self):
        super().setUp()
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

    def test_agreement_with_equipment(self):
        agreement = Form(self.env["service.agreement"])
        agreement.name = "Test Agreement"
        agreement.partner_id = self.partner_1
        agreement.type_id = self.agreement_type
        agreement.cycle_id = self.cycle
        agreement.meter_reading_status = True

        with agreement.agreement_line.new() as agreement_line:
            agreement_line.product_id = self.product_1
            agreement_line.quantity = 1
            agreement_line.price_unit = 100
            agreement_line.equipment_id = self.equipment
            agreement_line.meter_id = self.meter

        agreement = agreement.save()
        agreement.contract_open()
        agreement.service_equipment()

        meter_reading = Form(self.env["service.meter.reading"])
        meter_reading.meter_id = self.meter
        meter_reading.counter_value = 100
        meter_reading.date = self.date_range.date_start
        meter_reading.save()

        meter_reading = Form(self.env["service.meter.reading"])
        meter_reading.meter_id = self.meter
        meter_reading.counter_value = 200
        meter_reading.date = self.date_range.date_end
        meter_reading.save()

        wizard = Form(self.env["service.billing.preparation"].with_context(active_ids=[agreement.id]))
        wizard.service_period_id = self.date_range
        wizard = wizard.save()
        action = wizard.do_billing_preparation()

        consumptions = self.env["service.consumption"].search(action["domain"])

        wizard = Form(self.env["service.billing"].with_context(active_ids=consumptions.ids))
        wizard.journal_id = self.journal
        wizard = wizard.save()
        action = wizard.do_billing()

        invoices = self.env["account.move"].search(action["domain"])
        invoices.action_post()
        # invoices.generate_excel_meters_report()

        self.equipment.compute_totals()
        self.equipment.invoice_button()
        self.equipment.create_meters_button()

    def test_equipment_operation(self):
        agreement = Form(self.env["service.agreement"])
        agreement.name = "Test Agreement"
        agreement.partner_id = self.partner_1
        agreement.type_id = self.agreement_type
        agreement.cycle_id = self.cycle

        agreement = agreement.save()

        wizard = Form(self.env["service.equi.operation"].with_context(active_id=self.equipment.id, default_state="add"))
        wizard.service_period_id = self.date_range
        wizard.agreement_id = agreement
        wizard = wizard.save()
        wizard.do_operation()

    def test_product_serial(self):
        category = Form(self.env["product.category"])
        category.name = "Test Category"
        category.equi_type_required = True
        category = category.save()

        product = Form(self.env["product.product"])
        product.name = "Test Product"
        product.categ_id = category
        product.equi_type_id = self.equipment_type
        product = product.save()

        self.env["stock.lot"].create(
            {
                "name": "Test Serial",
                "product_id": product.id,
            }
        )
