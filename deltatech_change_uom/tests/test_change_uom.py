# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestChangeUoM(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product = self.env["product.template"].create(
            {
                "name": "Test Product",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "uom_po_id": self.env.ref("uom.product_uom_unit").id,
            }
        )

    def test_wizard(self):
        wizard = Form(self.env["product.change.uom"].with_context(active_id=self.product.id))
        wizard.uom_id = self.env.ref("uom.product_uom_dozen")
        wizard.uom_po_id = self.env.ref("uom.product_uom_dozen")
        wizard = wizard.save()
        wizard.do_change()
