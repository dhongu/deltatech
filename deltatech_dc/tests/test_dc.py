# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestDC(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_a = self.env["res.partner"].create({"name": "Test"})
        self.product_a = self.env["product.product"].create(
            {
                "name": "Test A",
            }
        )

    def test_create_dc(self):
        form_dc = Form(self.env["deltatech.dc"])
        form_dc.name = "Test"
        form_dc.date = "2021-01-01"
        form_dc.product_id = self.product_a
        form_dc.save()

    def test_lot(self):
        form_lot = Form(self.env["stock.lot"])
        form_lot.name = "Test"
        form_lot.product_id = self.product_a
        lot = form_lot.save()
        lot.production_date = "2021-01-01"
        lot._get_dates(product_id=self.product_a.id)
