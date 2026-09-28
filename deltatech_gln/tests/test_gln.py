import importlib.util
from pathlib import Path

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

VALID_GLN = "9780471117094"
OTHER_GLN = "4006381333931"


class TestResPartner(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner", "gln": VALID_GLN})

    def test_check_gln(self):
        # Check if the GLN is correctly set
        self.assertEqual(self.partner.gln, VALID_GLN, "GLN is not correctly set")

    def test_gln_is_standard_identifier(self):
        """`gln` is kept in the standard identifiers, in both directions."""
        self.assertEqual(self.partner.additional_identifiers, {"EAN_GLN": VALID_GLN})
        self.partner.gln = False
        self.assertFalse(self.partner.additional_identifiers)
        self.partner._set_additional_identifier("EAN_GLN", OTHER_GLN)
        self.assertEqual(self.partner.gln, OTHER_GLN)
        if "global_location_number" in self.partner._fields:
            self.assertEqual(self.partner.global_location_number, OTHER_GLN)

    def test_gln_invalid(self):
        with self.assertRaises(ValidationError):
            self.partner.gln = "1234567890"

    def test_search_gln(self):
        Partner = self.env["res.partner"]
        other = Partner.create({"name": "Other Partner", "gln": OTHER_GLN})
        without = Partner.create({"name": "Partner without GLN"})
        self.assertEqual(Partner.search([("gln", "=", VALID_GLN)]), self.partner)
        self.assertEqual(Partner.search([("gln", "in", [VALID_GLN, OTHER_GLN])]), self.partner | other)
        self.assertEqual(Partner.search([("gln", "ilike", "7804711")]), self.partner)
        self.assertIn(without, Partner.search([("gln", "not ilike", "7804711")]))
        self.assertNotIn(self.partner, Partner.search([("gln", "!=", VALID_GLN)]))
        self.assertIn(other, Partner.search([("gln", "!=", VALID_GLN)]))
        self.assertIn(without, Partner.search([("gln", "!=", VALID_GLN)]))
        self.assertIn(without, Partner.search([("gln", "=", False)]))
        self.assertNotIn(self.partner, Partner.search([("gln", "=", False)]))
        self.assertIn(self.partner, Partner.search([("gln", "!=", False)]))

    def test_migration_from_19(self):
        """The 20.0 migration moves the old `gln` column into the standard identifiers."""
        path = Path(__file__).parents[1] / "migrations" / "20.0.1.1.0" / "post-migration.py"
        spec = importlib.util.spec_from_file_location("odoo.addons.deltatech_gln.migrations.post_migration", path)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)

        Partner = self.env["res.partner"]
        to_fill = Partner.create({"name": "To fill"})
        kept = Partner.create({"name": "Kept", "gln": OTHER_GLN})
        malformed = Partner.create({"name": "Malformed"})
        self.env.flush_all()
        cr = self.env.cr
        # the 19.0 column, as left in place by the ORM once the field is no longer stored
        cr.execute("ALTER TABLE res_partner ADD COLUMN gln varchar")
        cr.execute("UPDATE res_partner SET gln = %s WHERE id IN %s", [VALID_GLN, (to_fill.id, kept.id)])
        cr.execute("UPDATE res_partner SET gln = %s WHERE id = %s", ["1234567890", malformed.id])

        with self.assertLogs("odoo.addons.deltatech_gln", level="WARNING") as logs:
            migration.migrate(cr, "19.0.1.1.0")

        self.assertEqual(to_fill.gln, VALID_GLN)
        self.assertEqual(kept.gln, OTHER_GLN, "an existing standard value must not be overwritten")
        self.assertFalse(malformed.gln)
        output = "\n".join(logs.output)
        self.assertIn(str(kept.id), output)
        self.assertIn(str(malformed.id), output)
