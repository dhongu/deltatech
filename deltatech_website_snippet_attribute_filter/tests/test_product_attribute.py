# ©  2023 Deltatech - Dorin Hongu
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestProductAttribute(TransactionCase):
    def setUp(self):
        super().setUp()

    def test_get_attribute_values(self):
        attribute = self.env["product.attribute"].create({"name": "Test"})
        values = self.env["product.attribute.value"].create(
            [{"name": "Test", "attribute_id": attribute.id}, {"name": "Test2", "attribute_id": attribute.id}]
        )
        # get_attribute_values
        attribute.get_attribute_values()
        attribute.get_attribute_values(attribute_value_ids="{},{}".format(values.ids[0], values.ids[1]))
        attribute.get_attribute_values(attribute_value_ids=values.ids)
