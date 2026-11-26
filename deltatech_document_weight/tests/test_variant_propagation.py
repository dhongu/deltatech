from odoo.tests import tagged
from odoo.tests.common import TransactionCase

PARAM = "deltatech_document_weight.propagate_variants"


@tagged("post_install", "-at_install")
class TestVariantPropagation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.attribute = cls.env["product.attribute"].create(
            {
                "name": "Dynamic size",
                "create_variant": "dynamic",
                "value_ids": [(0, 0, {"name": "S"}), (0, 0, {"name": "M"}), (0, 0, {"name": "L"})],
            }
        )
        cls.template = cls.env["product.template"].create(
            {
                "name": "Dynamic product",
                "attribute_line_ids": [
                    (0, 0, {"attribute_id": cls.attribute.id, "value_ids": [(6, 0, cls.attribute.value_ids.ids)]})
                ],
            }
        )

    def _combination(self, index):
        ptav = self.template.attribute_line_ids.product_template_value_ids[index]
        return ptav

    def _enable(self, value):
        self.env["ir.config_parameter"].sudo().set_bool(PARAM, value)

    def test_off_by_default(self):
        self.assertFalse(self.env["product.template"]._document_weight_propagation_enabled())

    def test_new_variants_do_not_get_the_values_when_off(self):
        first = self.template._create_product_variant(self._combination(0))
        first.write({"weight": 5.0, "volume": 2.0, "l10n_ro_net_weight": 4.0})
        second = self.template._create_product_variant(self._combination(1))
        self.assertEqual(second.weight, 0.0)

    def test_new_variants_get_the_values_when_on(self):
        self._enable(True)
        first = self.template._create_product_variant(self._combination(0))
        first.write({"weight": 5.0, "volume": 2.0, "l10n_ro_net_weight": 4.0})
        second = self.template._create_product_variant(self._combination(1))
        self.assertEqual((second.weight, second.volume, second.l10n_ro_net_weight), (5.0, 2.0, 4.0))
        # from the third variant on the template fields are 0: the source is an existing variant
        third = self.template._create_product_variant(self._combination(2))
        self.assertEqual((third.weight, third.volume, third.l10n_ro_net_weight), (5.0, 2.0, 4.0))

    def test_template_write_reaches_all_variants_when_on(self):
        self._enable(True)
        variants = self.template._create_product_variant(self._combination(0))
        variants |= self.template._create_product_variant(self._combination(1))
        self.template.write({"weight": 7.0, "volume": 1.0, "l10n_ro_net_weight": 6.0})
        self.assertEqual(variants.mapped("weight"), [7.0, 7.0])
        self.assertEqual(variants.mapped("volume"), [1.0, 1.0])
        self.assertEqual(variants.mapped("l10n_ro_net_weight"), [6.0, 6.0])

    def test_template_write_native_behaviour_when_off(self):
        # Odoo 20 writes the weight on all the variants by itself; the net weight only on a template
        # with a single variant
        variants = self.template._create_product_variant(self._combination(0))
        variants |= self.template._create_product_variant(self._combination(1))
        self.template.write({"weight": 7.0, "l10n_ro_net_weight": 6.0})
        self.assertEqual(variants.mapped("weight"), [7.0, 7.0])
        self.assertEqual(variants.mapped("l10n_ro_net_weight"), [0.0, 0.0])
