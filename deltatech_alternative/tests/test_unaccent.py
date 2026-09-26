# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase
from odoo.tools.sql import index_exists

from ..models.product import _create_trgm_index

REPLACED_UNACCENT = """
    SELECT 1
      FROM pg_proc p
      JOIN pg_depend d ON d.classid = 'pg_proc'::regclass AND d.objid = p.oid AND d.deptype = 'e'
      JOIN pg_extension e ON e.oid = d.refobjid AND e.extname = 'unaccent'
      JOIN pg_language l ON l.oid = p.prolang
     WHERE p.proname = 'unaccent' AND p.pronargs = 1 AND l.lanname = 'sql'
"""

UNACCENT_DEFINITIONS = """
    SELECT p.oid::regprocedure::text, p.provolatile, l.lanname, md5(pg_get_functiondef(p.oid))
      FROM pg_proc p
      JOIN pg_language l ON l.oid = p.prolang
     WHERE p.proname = 'unaccent'
     ORDER BY 1
"""


class TestUnaccent(TransactionCase):
    def test_failed_index_does_not_touch_unaccent(self):
        """A trigram index that cannot be built must not modify unaccent(text).

        Up to 18.0.2.1.8 the fallback replaced the extension's function with a
        SQL wrapper, which breaks restoring a dump of the database.
        """
        cr = self.env.cr
        cr.execute(UNACCENT_DEFINITIONS)
        before = cr.fetchall()
        with self.assertLogs("odoo.addons.deltatech_alternative.models.product", level="WARNING"):
            _create_trgm_index(
                cr,
                "deltatech_alternative_test_trgm_idx",
                "product_alternative",
                "deltatech_alternative_missing_function(name) gin_trgm_ops",
            )
        self.assertFalse(index_exists(cr, "deltatech_alternative_test_trgm_idx"))
        cr.execute(UNACCENT_DEFINITIONS)
        after = [row for row in cr.fetchall() if row[0] in {r[0] for r in before}]
        self.assertEqual(before, after)

    def test_extension_unaccent_not_replaced(self):
        """The module (installed or updated) never replaces the extension's function."""
        self.env.cr.execute(REPLACED_UNACCENT)
        self.assertFalse(self.env.cr.fetchone())

    def test_product_tmpl_id_indexed(self):
        self.assertTrue(index_exists(self.env.cr, "product_alternative__product_tmpl_id_index"))
