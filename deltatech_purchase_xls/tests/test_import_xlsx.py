# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import base64

from odoo.modules.module import get_module_resource
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestImportXLS(TransactionCase):
    def setUp(self):
        super().setUp()

    def test_xlsx_file_import(self):
        order_file_path = get_module_resource(
            "deltatech_purchase_xls",
            "tests",
            "test.xlsx",
        )
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
