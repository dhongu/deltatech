# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestCycle(TransactionCase):
    def test_create_cycle(self):
        cycle = Form(self.env["service.cycle"])
        cycle.name = "Test Cycle"
        cycle.value = 1
        cycle.unit = "day"
        cycle = cycle.save()
        cycle.get_cycle()
