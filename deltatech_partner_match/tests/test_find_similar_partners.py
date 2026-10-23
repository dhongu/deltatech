# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestFindSimilarPartners(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ro = cls.env.ref("base.ro")
        Partner = cls.env["res.partner"]

        def partner(name, **vals):
            return Partner.create({"name": name, "country_id": ro.id, **vals})

        cls.ion = partner("Ion Pmatchescu", phone="0722 914 456", street="Str. Lalelelor nr. 5", city="Cluj-Napoca")
        cls.ana = partner("Ana Pmatchescu", phone="+40 722 914 456", city="Cluj-Napoca")
        cls.maria = partner("Maria Pmatchescu", email="Maria.Pmatch@Example.com ")
        cls.alfa = partner("Pmatch Alfa SRL", vat="RO18547290", is_company=True)
        cls.other = partner("Pmatch Other", phone="0733 914 456")
        cls.env.flush_all()

    def _find(self, values, **kwargs):
        return self.env["res.partner"]._find_similar_partners(values, **kwargs)

    def test_phone_candidates_scored(self):
        values = {
            "name": "Pmatchescu Ion",
            "phone": "0040722914456",
            "street": "Strada Lalelelor 5",
            "city": "Cluj Napoca",
        }
        result = self._find(values)
        self.assertEqual([item["partner"] for item in result], [self.ion, self.ana])
        best = result[0]
        self.assertEqual(best["reasons"], ["phone"])
        self.assertEqual(best["name_score"], 1.0)
        # street words count, as in the marketplace import: "str lalelelor nr 5" / "strada lalelelor 5"
        # share 2 of 5 words, so 0.6 * 1 + 0.25 * 0.4 + 0.15 * 1
        self.assertAlmostEqual(best["score"], 0.85)
        self.assertLess(result[1]["name_score"], 0.8, "a relative sharing the phone is another person")

    def test_phone_without_phone_sanitized(self):
        with patch.object(type(self.env["res.partner"]), "_partner_match_stored", return_value=False):
            result = self._find({"name": "Ion Pmatchescu", "phone": "+40722914456"})
        self.assertEqual({item["partner"] for item in result}, {self.ion, self.ana})

    def test_email_and_vat(self):
        result = self._find({"name": "Maria", "email": "maria.pmatch@example.com"})
        self.assertEqual([item["partner"] for item in result], [self.maria])
        self.assertEqual(result[0]["reasons"], ["email"])
        result = self._find({"name": "Alfa", "vat": "RO 018 547 290"})
        self.assertEqual([item["partner"] for item in result], [self.alfa])
        self.assertEqual(result[0]["reasons"], ["vat"])
        with patch.object(type(self.env["res.partner"]), "_partner_match_stored", return_value=False):
            result = self._find({"name": "Maria", "email": "MARIA.PMATCH@example.com"})
        self.assertEqual([item["partner"] for item in result], [self.maria])

    def test_keys_and_domain(self):
        values = {"name": "Ion Pmatchescu", "phone": "0722914456", "vat": "RO18547290"}
        self.assertEqual({item["partner"] for item in self._find(values, keys=("vat",))}, {self.alfa})
        result = self._find(values, domain=[("is_company", "=", False)])
        self.assertEqual({item["partner"] for item in result}, {self.ion, self.ana})
        self.assertEqual(len(self._find(values, limit=1)), 1)

    def test_no_strong_key(self):
        self.assertEqual(self._find({"name": "Ion Pmatchescu"}), [], "a name alone selects nobody")
        self.assertEqual(self._find({"name": "Ion Pmatchescu", "phone": "0000000"}), [])

    def test_county(self):
        """A village name exists in several counties: in another county the address does not count."""
        bacau, iasi = self.env.ref("base.RO_BC"), self.env.ref("base.RO_IS")
        self.ion.write({"state_id": bacau.id, "street": "Str. Principala 1", "city": "Satu Nou"})
        values = {"name": "Ion Pmatchescu", "phone": "0722914456", "street": "Str. Principala 1", "city": "Satu Nou"}
        same, other, unknown = (self._find(dict(values, county=county))[0] for county in ("BC", "Iași", "Necunoscut"))
        self.assertEqual(same["partner"], self.ion)
        self.assertAlmostEqual(same["score"], 1.0)
        self.assertAlmostEqual(other["score"], 0.6, msg="name only: street and city score 0")
        self.assertAlmostEqual(unknown["score"], 1.0, msg="an unknown county never lowers the score")
        self.assertAlmostEqual(self._find(dict(values, state_id=iasi.id))[0]["score"], 0.6)
        self.assertAlmostEqual(self._find(values)[0]["score"], 1.0, msg="no county given")
