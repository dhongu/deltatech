# See README.rst file on addons root folder for license details

import importlib.util
import json
from pathlib import Path

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import SQL

_PATH = Path(__file__).parent.parent / "migrations" / "19.0.1.2.6" / "pre-migration.py"


def _load():
    spec = importlib.util.spec_from_file_location("tb_pp_pre_migration", _PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@tagged("post_install", "-at_install")
class TestMigrationLastPurchasePrice(TransactionCase):
    """Runs the copy step on scratch tables, never on the real product tables."""

    def setUp(self):
        super().setUp()
        self.migration = _load()
        self.cr.execute("CREATE TABLE tb_pp_tmpl (id serial PRIMARY KEY, company_id int, last_purchase_price float8)")
        self.company = self.env.company
        self.company2 = self.env["res.company"].create({"name": "Second company"})

    def _prod_table(self, column_type):
        col = SQL(", last_purchase_price %s", SQL(column_type)) if column_type else SQL()
        self.cr.execute(
            SQL("CREATE TABLE tb_pp_prod (id serial PRIMARY KEY, product_tmpl_id int, active bool DEFAULT TRUE%s)", col)
        )

    def _tmpl(self, price, company=None):
        self.cr.execute(
            "INSERT INTO tb_pp_tmpl (company_id, last_purchase_price) VALUES (%s, %s) RETURNING id",
            (company.id if company else None, price),
        )
        return self.cr.fetchone()[0]

    def _prod(self, tmpl, value=None, active=True):
        if value is None:
            query = SQL("INSERT INTO tb_pp_prod (product_tmpl_id, active) VALUES (%s, %s) RETURNING id", tmpl, active)
        else:
            query = SQL(
                "INSERT INTO tb_pp_prod (product_tmpl_id, active, last_purchase_price) "
                "VALUES (%s, %s, %s::jsonb) RETURNING id",
                tmpl,
                active,
                value,
            )
        self.cr.execute(query)
        return self.cr.fetchone()[0]

    def _run(self):
        self.migration.copy_template_prices(self.cr, "tb_pp_tmpl", "tb_pp_prod")

    def _value(self, prod_id):
        self.cr.execute("SELECT last_purchase_price FROM tb_pp_prod WHERE id = %s", (prod_id,))
        return self.cr.fetchone()[0]

    def test_target_jsonb_company_template(self):
        self._prod_table("jsonb")
        prod = self._prod(self._tmpl(10, self.company))
        self._run()
        self.assertEqual(self._value(prod), {str(self.company.id): 10})

    def test_target_missing_is_created(self):
        self._prod_table(None)
        prod = self._prod(self._tmpl(7, self.company))
        self._run()
        self.assertEqual(self._value(prod), {str(self.company.id): 7})

    def test_shared_template_all_companies(self):
        self._prod_table("jsonb")
        prod = self._prod(self._tmpl(5))
        self._run()
        value = self._value(prod)
        self.assertEqual(value[str(self.company.id)], 5)
        self.assertEqual(value[str(self.company2.id)], 5)

    def test_existing_value_kept(self):
        self._prod_table("jsonb")
        prod = self._prod(self._tmpl(10, self.company), json.dumps({str(self.company.id): 99}))
        self._run()
        self.assertEqual(self._value(prod), {str(self.company.id): 99})

    def test_multi_variant_gets_price_inactive_skipped(self):
        self._prod_table("jsonb")
        tmpl = self._tmpl(3, self.company)
        v1, v2, v3 = self._prod(tmpl), self._prod(tmpl), self._prod(tmpl, active=False)
        self._run()
        key = str(self.company.id)
        self.assertEqual(self._value(v1), {key: 3})
        self.assertEqual(self._value(v2), {key: 3})
        self.assertIsNone(self._value(v3))

    def test_zero_price_ignored(self):
        self._prod_table("jsonb")
        prod = self._prod(self._tmpl(0, self.company))
        self._run()
        self.assertIsNone(self._value(prod))

    def test_numeric_target_converted_then_template_added(self):
        self._prod_table("float8")
        self.cr.execute("INSERT INTO tb_pp_prod (product_tmpl_id, last_purchase_price) VALUES (1, 4) RETURNING id")
        prod = self.cr.fetchone()[0]
        self._run()
        self.assertEqual(self._value(prod)[str(self.company.id)], 4)
