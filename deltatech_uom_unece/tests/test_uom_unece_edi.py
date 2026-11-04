# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestUomUneceEdi(TransactionCase):
    """În 20.0 toate documentele electronice citesc codul prin `uom.uom._get_unece_code()`.

    `account_edi_ubl_cii` are acum câmpul standard `unece_code` (unic) și
    a renunțat la `account.edi.common._get_uom_unece_code()`. Codul ales din
    nomenclator trebuie să bată câmpul standard și să poată fi folosit pe mai
    multe unități.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.kg = cls.env.ref("uom.product_uom_kgm")
        cls.xbx = cls.env.ref("deltatech_uom_unece.unece_xbx")

    def _box(self, name, factor, **vals):
        return self.env["uom.uom"].create(
            {"name": name, "relative_uom_id": self.kg.id, "relative_factor": factor, **vals}
        )

    def test_configured_code_wins_over_standard_field(self):
        box = self._box("Cutie 13 kg", 13, unece_code="XCT", unece_code_id=self.xbx.id)
        self.assertEqual(box._get_unece_code(), "XBX")

    def test_standard_field_used_when_module_field_empty(self):
        box = self._box("Cutie 13 kg", 13, unece_code="XCT")
        self.assertEqual(box._get_unece_code(), "XCT")

    def test_unit_without_code_keeps_core_behaviour(self):
        box = self._box("Cutie fără cod", 13)
        self.assertEqual(box._get_unece_code(), "C62")
        self.assertEqual(self.kg._get_unece_code(), "KGM")

    def test_code_can_be_shared_between_units(self):
        """Câmpul standard e unic; nomenclatorul permite același cod pe mai multe cutii."""
        box_13 = self._box("Cutie 13 kg", 13, unece_code_id=self.xbx.id)
        box_5 = self._box("Cutie 5 kg", 5, unece_code_id=self.xbx.id)
        self.assertEqual(box_13._get_unece_code(), "XBX")
        self.assertEqual(box_5._get_unece_code(), "XBX")
