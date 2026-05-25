# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestSplitMultiCodes(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product = self.env["product.template"].create({"name": "Test Product for Split"})
        self.Alternative = self.env["product.alternative"]

    def _make(self, name, sequence=10, hide=False):
        return self.Alternative.create(
            {
                "name": name,
                "product_tmpl_id": self.product.id,
                "sequence": sequence,
                "hide": hide,
            }
        )

    def _split_and_get(self, record):
        self.Alternative.split_multi_codes()
        return self.Alternative.search([("product_tmpl_id", "=", self.product.id)], order="id asc")

    # ------------------------------------------------------------------
    # Separatori simpli
    # ------------------------------------------------------------------

    def test_split_by_semicolon(self):
        self._make("CODE1;CODE2;CODE3")
        all_records = self._split_and_get(None)
        names = all_records.mapped("name")
        self.assertEqual(sorted(names), ["CODE1", "CODE2", "CODE3"])

    def test_split_by_comma(self):
        self._make("AAA,BBB,CCC")
        all_records = self._split_and_get(None)
        names = all_records.mapped("name")
        self.assertEqual(sorted(names), ["AAA", "BBB", "CCC"])

    def test_split_by_space(self):
        self._make("X1 X2 X3")
        all_records = self._split_and_get(None)
        names = all_records.mapped("name")
        self.assertEqual(sorted(names), ["X1", "X2", "X3"])

    # ------------------------------------------------------------------
    # Separatori cu spații suplimentare
    # ------------------------------------------------------------------

    def test_split_semicolon_with_spaces(self):
        self._make("CODE1; CODE2; CODE3")
        all_records = self._split_and_get(None)
        names = all_records.mapped("name")
        self.assertEqual(sorted(names), ["CODE1", "CODE2", "CODE3"])

    def test_split_comma_with_spaces(self):
        self._make("A1 , A2 , A3")
        all_records = self._split_and_get(None)
        names = all_records.mapped("name")
        self.assertEqual(sorted(names), ["A1", "A2", "A3"])

    # ------------------------------------------------------------------
    # Separatori mixti
    # ------------------------------------------------------------------

    def test_split_mixed_separators(self):
        self._make("C1; C2, C3 C4")
        all_records = self._split_and_get(None)
        names = all_records.mapped("name")
        self.assertEqual(sorted(names), ["C1", "C2", "C3", "C4"])

    # ------------------------------------------------------------------
    # Record fără separator — nu trebuie atins
    # ------------------------------------------------------------------

    def test_no_split_single_code(self):
        self._make("SINGLE")
        self.Alternative.split_multi_codes()
        remaining = self.Alternative.search([("product_tmpl_id", "=", self.product.id)])
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining.name, "SINGLE")

    # ------------------------------------------------------------------
    # Atribute moștenite (sequence, hide)
    # ------------------------------------------------------------------

    def test_inherited_attributes(self):
        self._make("P1;P2;P3", sequence=20, hide=True)
        self.Alternative.split_multi_codes()
        all_records = self.Alternative.search([("product_tmpl_id", "=", self.product.id)])
        for rec in all_records:
            self.assertEqual(rec.sequence, 20)
            self.assertTrue(rec.hide)

    # ------------------------------------------------------------------
    # Primul cod rămâne pe înregistrarea originală
    # ------------------------------------------------------------------

    def test_first_code_stays_on_original_record(self):
        rec = self._make("FIRST;SECOND;THIRD")
        original_id = rec.id
        self.Alternative.split_multi_codes()
        updated = self.Alternative.browse(original_id)
        self.assertEqual(updated.name, "FIRST")

    # ------------------------------------------------------------------
    # Înregistrare fără product_tmpl_id
    # ------------------------------------------------------------------

    def test_split_without_product_tmpl_id(self):
        orphan = self.Alternative.create({"name": "ORF1;ORF2", "product_tmpl_id": False})
        self.Alternative.split_multi_codes()
        results = self.Alternative.search([("id", "in", [orphan.id]), ("name", "=", "ORF1")])
        self.assertEqual(len(results), 1)
        new_code = self.Alternative.search([("name", "=", "ORF2"), ("product_tmpl_id", "=", False)])
        self.assertEqual(len(new_code), 1)

    # ------------------------------------------------------------------
    # Batch: maxim 5000 înregistrări procesate per apel
    # ------------------------------------------------------------------

    def test_batch_limit_not_exceeded(self):
        # Creăm 10 înregistrări cu câte 2 coduri — toate eligibile pentru split
        for i in range(10):
            self._make(f"BATCH{i}A;BATCH{i}B")

        # Prima execuție — toate 10 ar trebui procesate (sub limita de 5000)
        self.Alternative.split_multi_codes()
        all_records = self.Alternative.search([("product_tmpl_id", "=", self.product.id)])
        names = all_records.mapped("name")
        # Fiecare pereche a fost spartă, deci avem 20 de înregistrări individuale
        self.assertEqual(len(names), 20)
        for name in names:
            self.assertNotIn(";", name)
