# ©  2015-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestProductLocNewRecord(TransactionCase):
    def test_compute_loc_on_unsaved_product(self):
        # the rack / row / shelf / case are computed in the form, before the product is saved:
        # the search must not receive the NewId of the record
        with self.assertNoLogs("odoo.domains", level="WARNING"):
            with Form(self.env["product.template"]) as form:
                form.name = "Unsaved product location"
                self.assertFalse(form.loc_rack)
        template = form.save()
        self.env["product.warehouse.location"].create(
            {
                "product_id": template.id,
                "warehouse_id": self.env.ref("stock.warehouse0").id,
                "loc_rack": "R1",
            }
        )
        template.invalidate_recordset(["loc_rack"])
        self.assertEqual(template.loc_rack, "R1")
