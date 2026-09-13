# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestUomUneceEdi(TransactionCase):
    """`account_edi_ubl_cii` nu trece prin `uom.uom._get_unece_code()`.

    Are propria copie a logicii, pe modelul abstract `account.edi.common`, care
    citește direct dicționarul din standard. Fără puntea asta, un cod pus pe
    unitate s-ar aplica pe eTransport și ar fi ignorat pe facturi — tăcut, fiindcă
    ambele documente rămân valide față de schemă.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.edi = cls.env["account.edi.common"]
        cls.kg = cls.env.ref("uom.product_uom_kgm")

    def test_configured_code_is_used_in_edi_invoices(self):
        box = self.env["uom.uom"].create(
            {
                "name": "Cutie 13 kg",
                "relative_uom_id": self.kg.id,
                "relative_factor": 13,
                "unece_code_id": self.env.ref("deltatech_uom_unece.unece_xbx").id,
            }
        )
        self.assertEqual(self.edi._get_uom_unece_code(box), "XBX")

    def test_unit_without_code_keeps_core_behaviour(self):
        box = self.env["uom.uom"].create(
            {"name": "Cutie fără cod", "relative_uom_id": self.kg.id, "relative_factor": 13}
        )
        self.assertEqual(self.edi._get_uom_unece_code(box), "C62")
        self.assertEqual(self.edi._get_uom_unece_code(self.kg), "KGM")

    def test_core_gap_is_closed_for_invoices_too(self):
        """Metrul pătrat pleca „bucată" și pe factură, nu doar pe eTransport."""
        self.assertEqual(self.edi._get_uom_unece_code(self.env.ref("uom.product_uom_square_meter")), "MTK")
