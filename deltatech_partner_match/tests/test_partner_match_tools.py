# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.tests import BaseCase, tagged

from odoo.addons.deltatech_partner_match.tools import partner_match as pm


@tagged("post_install", "-at_install")
class TestPartnerMatchTools(BaseCase):
    def test_normalize_name(self):
        self.assertEqual(pm.normalize_name("S.C. Popescu Ion S.R.L."), "ion popescu")
        self.assertEqual(pm.normalize_name("Ștefănescu  Ana"), pm.normalize_name("ana stefanescu"))
        self.assertEqual(pm.normalize_name("Alfa GmbH"), pm.normalize_name("ALFA"))
        self.assertEqual(pm.normalize_name(False), "")
        self.assertEqual(pm.normalize_name("Sas Vasile"), "sas vasile", "a surname, not the French SAS")
        self.assertEqual(pm.normalize_name("Tary s.r.o."), "tary")
        self.assertEqual(pm.name_prefix("S.C. Popescu Ion SRL"), "pop")
        self.assertEqual(pm.normalize_text("Cluj-Napoca"), "cluj napoca")

    def test_normalize_address(self):
        self.assertEqual(pm.normalize_street("Str. Lalelelor nr. 5"), pm.normalize_street("Strada Lalelelor 5"))
        self.assertEqual(pm.normalize_city("Cluj-Napoca"), pm.normalize_city("cluj napoca"))

    def test_normalize_email(self):
        self.assertEqual(pm.normalize_email(" Ana@Example.COM"), "ana@example.com")
        self.assertEqual(pm.normalize_email('"Ana" <ana@example.com>'), "ana@example.com")
        self.assertIsNone(pm.normalize_email(""))

    def test_normalize_vat(self):
        self.assertEqual(pm.normalize_vat("RO 123.456"), "123456")
        self.assertEqual(pm.normalize_vat("ro0123456"), "123456")
        self.assertEqual(pm.normalize_vat("12345678"), "12345678")
        self.assertEqual(pm.normalize_vat("ESB12345678"), "ESB12345678")
        self.assertIsNone(pm.normalize_vat("RO"))
        self.assertIsNone(pm.normalize_vat("0000"))
        self.assertIsNone(pm.normalize_vat(None))

    def test_check_vat(self):
        self.assertTrue(pm.check_vat("RO18547290"))
        self.assertTrue(pm.check_vat("18547290"))
        self.assertFalse(pm.check_vat("RO18547291"))
        self.assertTrue(pm.check_vat("1800101221144"), "a CNP of 13 digits")
        self.assertFalse(pm.check_vat("ROABC"))
        self.assertIsNone(pm.check_vat(""))
        self.assertIsNone(pm.check_vat("US123456789"), "outside the EU")
        self.assertIsNone(pm.check_vat("18547290", "DE"), "no prefix, not Romanian")

    def test_normalize_phone(self):
        for phone in ("0722 913 456", "+40 722 913 456", "0040722913456", "40722913456", "722913456"):
            self.assertEqual(pm.normalize_phone(phone), "+40722913456", phone)
        self.assertEqual(pm.phone_key("0722 913 456"), pm.phone_key("+40722913456"))
        self.assertEqual(pm.phone_key("+40722913456"), "722913456")
        self.assertIsNone(pm.normalize_phone("0000000"))
        self.assertIsNone(pm.phone_key("0000000"), "a placeholder of one digit")
        self.assertIsNone(pm.phone_key("12345"), "too short")
        self.assertIsNone(pm.normalize_phone(False))
        self.assertEqual(pm.phone_key("1234567"), "1234567", "a refused number keeps its digits as key")

    def test_normalize_phone_rule(self):
        if not pm.phonenumbers:
            self.skipTest("phonenumbers is not installed")
        self.assertEqual(pm.normalize_phone("030 1234567", "DE"), "+49301234567")
        # possible (right length) but not valid: the rule of phone_validation refuses it, the plain
        # Romanian rules still give the E.164 form
        self.assertTrue(pm.phonenumbers.is_possible_number(pm.phonenumbers.parse("0122 913 456", "RO")))
        self.assertFalse(pm.phonenumbers.is_valid_number(pm.phonenumbers.parse("0122 913 456", "RO")))
        self.assertEqual(pm.normalize_phone("0122 913 456"), "+40122913456")

    def test_without_libraries(self):
        with (
            patch.object(pm, "phonenumbers", None),
            patch.object(pm, "unidecode", None),
            patch.object(pm, "rf_fuzz", None),
            patch.object(pm, "rf_process", None),
        ):
            self.assertFalse(pm.has_rapidfuzz())
            self.assertEqual(pm.normalize_name("Ștefănescu Ana"), "ana stefanescu")
            self.assertEqual(pm.normalize_phone("0722 913 456"), "+40722913456")
            self.assertEqual(pm.normalize_phone("+49 30 1234567", "DE"), "+49301234567")
            self.assertIsNone(pm.normalize_phone("030 1234567", "DE"), "national format of another country")
            self.assertEqual(pm.phone_key("030 1234567", "DE"), "301234567")
            self.assertEqual(pm.token_sort_ratio("Popescu Ion", "Ion Popescu"), 100)
            names = [pm.normalize_name(name) for name in ("Gheorghe Popescu", "Popescu Gheorghe", "Maria Ionescu")]
            self.assertEqual(pm.similar_pairs(names, 90), [(0, 1, 100)])
            self.assertIsNone(pm.similar_pairs(["a"] * (pm.DIFFLIB_MAX_BLOCK + 1), 90), "block too large")

    def test_name_similarity(self):
        self.assertEqual(pm.name_similarity("Popescu Ion", "Ion Popescu"), 1.0)
        self.assertAlmostEqual(pm.name_similarity("Ana Popescu", "Ion Popescu"), 0.67, places=2)
        self.assertGreater(pm.name_similarity("Ion Popescu", "Ioan Popescu"), 0.9)
        self.assertEqual(pm.name_similarity("", "Ion"), 0.0)
        # the whole-name ratio is higher on a shared surname: not for deciding a reuse
        self.assertGreater(pm.token_sort_ratio("Ana Popescu", "Ion Popescu"), 80)

    def test_similar_pairs(self):
        names = [pm.normalize_name(name) for name in ("Gheorghe Popescu", "Popescu Gheorghe", "Maria Ionescu")]
        self.assertEqual(pm.similar_pairs(names, 90), [(0, 1, 100)])
        self.assertEqual(pm.similar_pairs(names[:1], 90), [])

    def test_jaccard(self):
        self.assertEqual(pm.jaccard_similarity("Str. Lalelelor 5", "str lalelelor 5"), 1.0)
        self.assertEqual(pm.jaccard_similarity("", ""), 0.0)
        self.assertAlmostEqual(pm.jaccard_similarity("a b", "b c"), 1 / 3)

    def test_union_find(self):
        groups = pm.UnionFind()
        groups.union(3, 1)
        groups.union(1, 2)
        groups.find(7)
        self.assertEqual(groups.groups(), [[1, 2, 3]])
