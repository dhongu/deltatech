# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from psycopg2 import IntegrityError

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestUomUneceCode(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.kg = cls.env.ref("uom.product_uom_kgm")
        cls.unit = cls.env.ref("uom.product_uom_unit")
        cls.box_code = cls.env.ref("deltatech_uom_unece.unece_xbx")

    def test_empty_field_keeps_core_behaviour(self):
        """Câmpul necompletat nu schimbă nimic — condiția de a fi instalabil oriunde."""
        self.assertFalse(self.kg.unece_code_id)
        self.assertEqual(self.kg._get_unece_code(), "KGM")
        self.assertEqual(self.unit._get_unece_code(), "C62")

    def test_custom_unit_without_code_still_falls_back(self):
        """O unitate proprie fără cod rămâne `C62`, ca înainte de instalare."""
        box = self.env["uom.uom"].create({"name": "Cutie 13 kg", "relative_uom_id": self.kg.id, "relative_factor": 13})
        self.assertEqual(box._get_unece_code(), "C62")

    def test_custom_unit_with_code_is_declared_correctly(self):
        """Rostul modulului: o unitate proprie capătă un cod real."""
        box = self.env["uom.uom"].create(
            {
                "name": "Cutie 13 kg",
                "relative_uom_id": self.kg.id,
                "relative_factor": 13,
                "unece_code_id": self.box_code.id,
            }
        )
        self.assertEqual(box._get_unece_code(), "XBX")

    def test_explicit_code_overrides_core_mapping(self):
        """Codul explicit bate maparea din standard — altfel n-am putea corecta
        o mapare greșită a Odoo, care e jumătate din motivul modulului."""
        self.kg.unece_code_id = self.env.ref("deltatech_uom_unece.unece_tne")
        self.assertEqual(self.kg._get_unece_code(), "TNE")

    def test_empty_recordset_does_not_raise(self):
        """Standardul tolerează recordset-ul gol (linie de factură fără produs);
        override-ul nu are voie să introducă un `ensure_one`."""
        self.assertEqual(self.env["uom.uom"].browse()._get_unece_code(), "C62")


@tagged("post_install", "-at_install")
class TestCoreMappingGaps(TransactionCase):
    """Unitățile STANDARD pe care Odoo le declară greșit.

    `UOM_TO_UNECE_CODE` caută `uom.uom_square_meter` și `uom.uom_square_foot`,
    dar datele definesc `uom.product_uom_square_meter` și
    `uom.product_uom_square_foot`; mililitrul lipsește cu totul. Toate trei ies
    `C62` — „bucată" — în orice document electronic, fără nicio eroare.
    """

    def test_square_meter_is_declared_as_square_meter(self):
        self.assertEqual(self.env.ref("uom.product_uom_square_meter")._get_unece_code(), "MTK")

    def test_square_foot_is_declared_as_square_foot(self):
        self.assertEqual(self.env.ref("uom.product_uom_square_foot")._get_unece_code(), "FTK")

    def test_millilitre_is_declared_as_millilitre(self):
        self.assertEqual(self.env.ref("uom.product_uom_milliliter")._get_unece_code(), "MLT")

    def test_gap_is_real_without_the_data_fix(self):
        """Fără maparea din `data/uom_uom_data.xml` cele trei ar cădea pe `C62`.

        Dovedește că fixul de date chiar acoperă un gol, nu o presupunere: golim
        câmpul și cerem din nou codul, care cade înapoi în dicționarul standard.
        """
        for xmlid in (
            "uom.product_uom_square_meter",
            "uom.product_uom_square_foot",
            "uom.product_uom_milliliter",
        ):
            with self.subTest(uom=xmlid):
                uom = self.env.ref(xmlid)
                uom.unece_code_id = False
                self.assertEqual(uom._get_unece_code(), "C62")


@tagged("post_install", "-at_install")
class TestUneceCodeConstraints(TransactionCase):
    def test_code_must_be_unique(self):
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self.env["uom.unece.code"].create({"code": "KGM", "name": "Duplicate"})

    def test_code_format_is_enforced(self):
        """Nomenclatorul ANAF are coduri de 2-4 caractere alfanumerice majuscule.
        O valoare în afara tiparului ar fi respinsă abia la depunere."""
        for bad in ("kg", "K", "KILOGRAM", "K-G"):
            with self.subTest(code=bad):
                with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
                    with self.env.cr.savepoint():
                        self.env["uom.unece.code"].create({"code": bad, "name": "Bad"})


@tagged("post_install", "-at_install")
class TestNomenclature(TransactionCase):
    """Nomenclatorul încărcat din schema SAF-T publicată de ANAF."""

    def test_full_nomenclature_is_loaded(self):
        """Peste două mii de coduri, nu subsetul scris de mână de dinainte."""
        self.assertGreater(self.env["uom.unece.code"].search_count([]), 2000)

    def test_packaging_codes_are_marked_as_rec21(self):
        box = self.env.ref("deltatech_uom_unece.unece_xbx")
        self.assertEqual(box.code, "XBX")
        self.assertEqual(box.source, "rec21")

    def test_pallet_code_is_xpx_not_xpf(self):
        """`XPF` înseamnă „Pen"; paletul e `XPX`. Prima versiune scrisă din
        memorie greșea, iar nomenclatorul oficial a arătat-o."""
        self.assertEqual(self.env.ref("deltatech_uom_unece.unece_xpx").name, "Pallet")
        self.assertEqual(self.env.ref("deltatech_uom_unece.unece_xpf").name, "Pen")

    def test_four_character_code_is_accepted(self):
        """`XLTR` e în nomenclator, deși schema eTransport acceptă doar 2-3
        caractere: constrângerea nu are voie să respingă un cod valid în SAF-T."""
        self.assertEqual(self.env.ref("deltatech_uom_unece.unece_xltr").code, "XLTR")

    def test_romanian_names_are_translated(self):
        code = self.env.ref("deltatech_uom_unece.unece_kgm")
        if not self.env["res.lang"].search([("code", "=", "ro_RO")]):
            self.skipTest("Romanian is not loaded on this database.")
        self.assertEqual(code.with_context(lang="ro_RO").name, "kilogram")
        self.assertEqual(self.env.ref("deltatech_uom_unece.unece_xbx").with_context(lang="ro_RO").name, "Cutie")
