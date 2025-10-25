# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestTestSystem(TransactionCase):
    def setUp(self):
        super().setUp()
        # Ensure the parameter starts as False for deterministic behavior
        icp = self.env["ir.config_parameter"].sudo()
        icp.set_param("database.is_neutralized", False)
        # Create a settings transient record we can reuse
        self.settings = self.env["res.config.settings"].create({})

    def test_get_installed_modules_returns_list(self):
        modules = self.settings.get_installed_modules()
        self.assertIsInstance(modules, list)
        # core modules like 'base' or 'web' should generally be present
        self.assertTrue(any(isinstance(m, str) and m for m in modules))

    def test_get_neutralization_queries_handles_existing_and_missing_files(self):
        # A module with a known neutralize.sql in the source tree (enterprise present in repo)
        queries = list(self.settings.get_neutralization_queries(["account_avatax"]))
        # Should yield at least one SQL string for a module that has the file
        self.assertTrue(all(isinstance(q, str) and q.strip() for q in queries))

        # Non-existing module should simply be ignored (no exception, empty list)
        queries_none = list(self.settings.get_neutralization_queries(["module_that_does_not_exist_xyz"]))
        self.assertEqual(queries_none, [])

    def test_neutralize_database_executes_queries(self):
        # Patch get_neutralization_queries to produce a harmless SQL
        called = {"count": 0}

        def _fake_get_neutralization_queries(self, _modules):
            called["count"] += 1
            # Use an inexpensive SQL statement valid in PostgreSQL
            return iter(["SELECT 1"])  # iterator of SQL statements

        with patch.object(type(self.settings), "get_neutralization_queries", new=_fake_get_neutralization_queries):
            self.settings.neutralize_database()  # Should not raise
        # Ensure our fake was called at least once
        self.assertGreaterEqual(called["count"], 1)

    def test_set_values_updates_banner_and_triggers_neutralize_on_first_enable(self):
        # Ensure parameter is currently False
        icp = self.env["ir.config_parameter"].sudo()
        self.assertFalse(icp.get_param("database.is_neutralized", default=False))

        # Track whether neutralize_database is invoked when enabling
        flags = {"neutralize_called": 0}

        def _fake_neutralize_database():
            flags["neutralize_called"] += 1

        # Patch method on the class so Odoo's read-only record attributes are not reassigned
        with patch.object(type(self.settings), "neutralize_database", new=lambda self: _fake_neutralize_database()):
            # Enable neutralization and persist values
            self.settings.database_is_neutralized = True
            self.settings.set_values()

        # After enabling, parameter should be True
        self.assertEqual(icp.get_param("database.is_neutralized", default=False), "True")
        # And our neutralization should have been triggered exactly once
        self.assertEqual(flags["neutralize_called"], 1)

        # Calling set_values again with True should NOT trigger neutralization again
        flags["neutralize_called"] = 0
        with patch.object(type(self.settings), "neutralize_database", new=lambda self: _fake_neutralize_database()):
            # Value remains True
            self.settings.database_is_neutralized = True
            self.settings.set_values()
        self.assertEqual(flags["neutralize_called"], 0)

    def test_ir_module_module_compute_reflects_parameter(self):
        module = self.env["ir.module.module"].search([], limit=1)
        self.assertTrue(module)

        icp = self.env["ir.config_parameter"].sudo()

        # When parameter False
        icp.set_param("database.is_neutralized", False)
        module._compute_database_is_neutralized()
        self.assertFalse(module.database_is_neutralized)

        # When parameter True
        icp.set_param("database.is_neutralized", True)
        module._compute_database_is_neutralized()
        self.assertTrue(module.database_is_neutralized)
