# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestServiceBase(TransactionCase):
    def test_create_cycle(self):
        cycle = Form(self.env["service.cycle"])
        cycle.name = "Test Cycle"
        cycle.value = 1
        cycle.unit = "day"
        cycle = cycle.save()
        cycle.get_cycle()

    def test_create_data_range(self):
        data_range = Form(self.env["service.date.range"])
        data_range.name = "Test Data Range"
        data_range.date_start = "2020-01-01"
        data_range.date_end = "2020-01-31"
        data_range.save()

    def test_generate_date_range(self):
        self.env["service.date.range"].generate_date_range()
