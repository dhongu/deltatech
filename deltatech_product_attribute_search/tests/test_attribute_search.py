# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProductAttributeSearch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.variety = cls.env["product.attribute"].create(
            {
                "name": "Variety",
                "create_variant": "always",
                "value_ids": [
                    (0, 0, {"name": "Gala Mast"}),
                    (0, 0, {"name": "Idared"}),
                ],
            }
        )
        cls.size = cls.env["product.attribute"].create(
            {
                "name": "Size",
                "create_variant": "always",
                "value_ids": [
                    (0, 0, {"name": "70/75 mm"}),
                    (0, 0, {"name": "80/85 mm"}),
                ],
            }
        )
        cls.template = cls.env["product.template"].create(
            {
                "name": "Apples",
                "type": "consu",
                "attribute_line_ids": [
                    (0, 0, {"attribute_id": cls.variety.id, "value_ids": cls.variety.value_ids.ids}),
                    (0, 0, {"attribute_id": cls.size.id, "value_ids": cls.size.value_ids.ids}),
                ],
            }
        )
        # A second template sharing one variety, so a search on the variety alone
        # cannot be satisfied by the template name.
        cls.other_template = cls.env["product.template"].create(
            {
                "name": "Pears",
                "type": "consu",
                "attribute_line_ids": [
                    (0, 0, {"attribute_id": cls.variety.id, "value_ids": cls.variety.value_ids[1].ids}),
                ],
            }
        )

    def _name_search(self, query, **kwargs):
        return self.env["product.product"].name_search(query, **kwargs)

    def _found(self, query, **kwargs):
        return self.env["product.product"].browse([res[0] for res in self._name_search(query, **kwargs)])

    def test_search_by_attribute_value(self):
        """The value of an attribute finds the variants carrying it."""
        found = self._found("Gala Mast")
        self.assertTrue(found, "an attribute value alone finds nothing without this module")
        self.assertEqual(
            found,
            self.template.product_variant_ids.filtered(
                lambda p: "Gala Mast" in p.product_template_variant_value_ids.mapped("name")
            ),
        )

    def test_search_by_attribute_value_across_templates(self):
        """A shared value finds the variants of every template using it."""
        found = self._found("Idared")
        self.assertEqual(
            found.product_tmpl_id,
            self.template | self.other_template,
            "the search must not stop at the first template",
        )

    def test_search_single_value_attribute_line(self):
        """A value used on a single-variant template still matches.

        `Pears` has one variety, so Odoo leaves that value out of the variant's name
        and out of `product_template_variant_value_ids`. The pears are Idared all the
        same, and a search that skipped them would look like missing data.
        """
        pear = self.other_template.product_variant_ids
        self.assertEqual(len(pear), 1)
        self.assertNotIn("Idared", pear.display_name)
        self.assertIn(pear, self._found("Idared"))

    def test_search_mixing_name_and_attribute(self):
        """Tokens are ANDed, so a query can mix the template name and a value."""
        found = self._found("apples gala")
        self.assertEqual(len(found), 2, "two sizes of Gala Mast apples")
        self.assertEqual(found.product_tmpl_id, self.template)
        # Same words, no variant carries both: the template name excludes the pears.
        self.assertFalse(self._found("pears gala"))

    def test_search_mixing_two_attributes(self):
        """A query can mix values coming from two different attributes."""
        found = self._found("gala 80/85")
        self.assertEqual(len(found), 1)
        self.assertEqual(set(found.product_template_variant_value_ids.mapped("name")), {"Gala Mast", "80/85 mm"})

    def test_search_partial_token(self):
        """A prefix is enough — the user does not have to know the full value."""
        self.assertEqual(self._found("apples ga"), self._found("apples gala"))

    def test_attribute_excluded_from_search(self):
        """An attribute marked as not searchable stops matching."""
        self.size.search_ok = False
        self.assertFalse(self._found("80/85"), "values of a non-searchable attribute must not match")
        self.assertTrue(self._found("gala"), "the other attribute keeps working")

    def test_core_results_come_first(self):
        """Core answers first; the attribute matches only top up what it left."""
        # The reference is on one variant, the word it contains is on the others as an
        # attribute value: the one core matches has to come out on top.
        coded = self.template.product_variant_ids[-1]
        coded.default_code = "GALA-13"
        results = self._name_search("gala")
        self.assertEqual(
            results[0][0],
            coded.id,
            "a match on the internal reference must not be pushed down by attribute matches",
        )

    def test_limit_is_respected(self):
        """The limit applies to the whole result, core plus attribute matches."""
        self.assertEqual(len(self._name_search("apples", limit=2)), 2)
        self.assertEqual(len(self._name_search("apples gala", limit=1)), 1)

    def test_no_query_without_tokens(self):
        """An empty query keeps core's behaviour."""
        self.assertEqual(
            self._name_search("", limit=5),
            self.env["product.product"].name_search("", limit=5),
        )

    def test_negative_operator_untouched(self):
        """`not ilike` is left to core — this module only adds matches."""
        domain = self.env["product.product"]._attribute_search_domain("not ilike", "gala")
        self.assertTrue(domain.is_false(), "negative operators must not be extended")

    def test_too_many_tokens_is_left_to_core(self):
        """A pasted line is not a search; it must not cost one query per word."""
        pasted = "apples gala mast 70/75 mm box 13 kg lidl"
        domain = self.env["product.product"]._attribute_search_domain("ilike", pasted)
        self.assertTrue(domain.is_false())

    def test_display_name_search(self):
        """`display_name` searches — search views, imports — see values too."""
        found = self.env["product.product"].search([("display_name", "ilike", "Gala Mast")])
        self.assertTrue(found)
        self.assertEqual(found.product_tmpl_id, self.template)
