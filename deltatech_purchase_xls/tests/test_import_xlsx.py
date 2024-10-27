# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import base64

from odoo import fields
from odoo.tests import Form
from odoo.tests.common import TransactionCase

# from odoo.modules.module import get_module_resource
from odoo.tools import file_path


class TestImportXLS(TransactionCase):
    def setUp(self):
        super().setUp()

    def test_xlsx_file_import(self):
        order_file_path = file_path("deltatech_purchase_xls/tests/test.xlsx")
        order_file = base64.b64encode(open(order_file_path, "rb").read())

        order_form = Form(self.env["purchase.order"])
        order_form.partner_id = self.env["res.partner"].create({"name": "vendor"})

        order = order_form.save()

        wizard = self.env["import.purchase.line"].with_context(active_id=order.id, active_model="purchase.order")
        wizard_form = Form(wizard)
        wizard_form.data_file = order_file
        wizard_form.new_product = True
        wizard_form.has_header = True
        wizard = wizard_form.save()
        wizard.do_import()

    def test_xlsx_file_export(self):
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "is_storable": True,
                "purchase_method": "purchase",
            }
        )

        # Create a purchase order
        self.purchase_order = self.env["purchase.order"].create(
            {
                "partner_id": self.env.ref("base.res_partner_1").id,
                "date_order": fields.Date.today(),
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_qty": 10,
                            "product_uom": self.env.ref("uom.product_uom_unit").id,
                            "price_unit": 100,
                            "date_planned": fields.Date.today(),
                        },
                    )
                ],
            }
        )
        wizard = self.env["export.purchase.line"].with_context(
            active_ids=self.purchase_order.id, active_model="purchase.order"
        )
        wizard_form = Form(wizard)
        wizard = wizard_form.save()
        wizard.do_export()
