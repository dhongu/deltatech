# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests.common import TransactionCase


class TestOrderPoint(TransactionCase):
    def test_create_orderpoint(self):
        # se va crea un produs si se va verfica daca se creaza si un orderpoint
        product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "categ_id": self.env.ref("product.product_category_all").id,
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "uom_po_id": self.env.ref("uom.product_uom_unit").id,
                "default_code": "TEST",
                "barcode": "123456789",
            }
        )
        orderpoint = self.env["stock.warehouse.orderpoint"].search([("product_id", "=", product.id)])
        self.assertTrue(orderpoint)
