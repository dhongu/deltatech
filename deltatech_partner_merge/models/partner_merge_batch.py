# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

import logging
import time

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import SQL

from . import sql_queries as Q

_logger = logging.getLogger(__name__)

CATEGORY_HELP = {
    "A": "one record holds the documents, the rest are completely empty",
    "B": "documents on a single record only",
    "C": "invoices on more than one record",
    "D": "unreconciled balance on more than one record",
}


class PartnerMergeBatch(models.Model):
    _name = "partner.merge.batch"
    _description = "Bulk merge of partners duplicated on the same VAT"
    _order = "id desc"

    name = fields.Char(required=True, default=lambda self: self.env._("Merge batch"))
    state = fields.Selection(
        [("draft", "Draft"), ("analyzed", "Analyzed"), ("simulated", "Simulated"), ("done", "Applied")],
        default="draft",
        readonly=True,
        copy=False,
    )
    category_ids = fields.Char(
        string="Categories",
        default="A,B",
        required=True,
        help="Which groups enter the batch, comma separated. "
        "A: one record holds the documents, the rest are empty. "
        "B: documents on a single record. "
        "C: invoices spread over several records. "
        "D: unreconciled balance on several records. "
        "C and D change accounting figures — handle them with the accountant.",
    )
    group_limit = fields.Integer(
        default=200,
        help="How many groups in this batch. 0 = all eligible ones. The de-duplication step has a "
        "fixed cost of about 40 seconds regardless of size, so very small batches are inefficient.",
    )
    archive_instead_of_delete = fields.Boolean(
        string="Archive instead of delete",
        help="Absorbed records are deactivated rather than removed. Slower to clean up afterwards, "
        "but recoverable without restoring a backup. Recommended for the first production runs.",
    )
    line_ids = fields.One2many("partner.merge.batch.line", "batch_id", readonly=True)
    group_count = fields.Integer(compute="_compute_counts", store=True)
    record_count = fields.Integer(string="Records to absorb", compute="_compute_counts", store=True)
    classification = fields.Text(readonly=True, help="All groups by category and guard, as of the analysis.")
    report = fields.Text(readonly=True)
    missing_index_count = fields.Integer(readonly=True)

    @api.depends("line_ids", "line_ids.absorbed_count")
    def _compute_counts(self):
        for batch in self:
            batch.group_count = len(batch.line_ids)
            batch.record_count = sum(batch.line_ids.mapped("absorbed_count"))

    # ------------------------------------------------------------------ helpers

    def _categories(self):
        cats = [c.strip().upper() for c in (self.category_ids or "").split(",") if c.strip()]
        unknown = [c for c in cats if c not in CATEGORY_HELP]
        if unknown:
            raise UserError(self.env._("Unknown categories: %s", ", ".join(unknown)))
        if not cats:
            raise UserError(self.env._("Pick at least one category."))
        return cats

    def _table_exists(self, cr, table):
        cr.execute("SELECT to_regclass(%s) IS NOT NULL", (table,))
        return cr.fetchone()[0]

    def _face_sql(self, cr):
        """BUILD_FACE with the sub-queries whose tables are missing replaced by 0,
        so the module depends on `base` only."""
        parts = {}
        for key, (table, expr) in Q.FACE_PARTS.items():
            parts[key] = expr if self._table_exists(cr, table) else "0"
        return Q.BUILD_FACE.format(**parts)

    def _guard_single_batch(self):
        other = self.search([("state", "in", ("analyzed", "simulated")), ("id", "!=", self.id)], limit=1)
        if other:
            raise UserError(
                self.env._(
                    "Batch %s is still in progress. The working tables are shared, so only one batch "
                    "can be prepared at a time. Apply it or reset it to draft first.",
                    other.display_name,
                )
            )

    # ------------------------------------------------------------------ step 1-2

    def action_analyze(self):
        """Builds the working tables and the batch lines. Touches no business data."""
        self.ensure_one()
        self._guard_single_batch()
        cr = self.env.cr
        cats = self._categories()

        cr.execute(Q.FK_COLUMNS_WITHOUT_INDEX)
        missing = cr.fetchall()

        t0 = time.time()
        cr.execute(SQL(self._face_sql(cr)))
        cr.execute(SQL(Q.BUILD_GROUP))
        cr.execute(SQL(Q.BUILD_MAP, cats, self.group_limit or None))
        cr.execute("CREATE INDEX ON pm_map(vat_n)")
        cr.execute(Q.CHECK_NO_CHAIN)
        chained = cr.fetchone()[0]
        if chained:
            raise UserError(
                self.env._(
                    "Inconsistent batch: %s records point at a master that is itself absorbed. "
                    "This should not happen — do not apply, and report it.",
                    chained,
                )
            )
        cr.execute(SQL(Q.BUILD_SNAPSHOT))
        cr.execute("ANALYZE pm_face; ANALYZE pm_group; ANALYZE pm_map")

        self.line_ids.unlink()
        cr.execute(
            """SELECT m.master_id, m.vat_n, g.categorie, count(*),
                      array_agg(m.old_id ORDER BY m.old_id), s.denumiri_absorbite
                 FROM pm_map m
                 JOIN pm_group g ON g.vat_n = m.vat_n
                 LEFT JOIN pm_snapshot s ON s.master_id = m.master_id
                GROUP BY m.master_id, m.vat_n, g.categorie, s.denumiri_absorbite
                ORDER BY m.vat_n"""
        )
        Line = self.env["partner.merge.batch.line"]
        vals = [
            {
                "batch_id": self.id,
                "master_id": master_id,
                "vat_normalized": vat_n,
                "category": cat,
                "absorbed_count": n,
                "absorbed_ids": ", ".join(str(i) for i in ids),
                "absorbed_names": names or "",
            }
            for master_id, vat_n, cat, n, ids, names in cr.fetchall()
        ]
        Line.create(vals)

        cr.execute(
            "SELECT categorie, coalesce(blocaj, 'eligible'), count(*), sum(membri) - count(*) "
            "FROM pm_group GROUP BY 1, 2 ORDER BY 1, 2"
        )
        rows = cr.fetchall()
        width = max((len(r[1]) for r in rows), default=10)
        self.classification = "\n".join(
            f"{cat}  {blocaj:<{width}}  {grupuri:>6} groups  {fise:>6} records" for cat, blocaj, grupuri, fise in rows
        )
        self.missing_index_count = len(missing)
        self.state = "analyzed"
        self.report = self.env._(
            "Analysis done in %(sec).1f s. %(groups)s groups, %(records)s records to absorb.\n"
            "%(idx)s foreign-key columns towards res_partner still lack an index.",
            sec=time.time() - t0,
            groups=len(vals),
            records=sum(v["absorbed_count"] for v in vals),
            idx=len(missing),
        )
        return True

    # ------------------------------------------------------------------ step 3-6

    def _dedupe(self, cr, mode):
        """Collapses rows that would collide on a unique index after the remap."""
        out = []
        cr.execute(SQL(Q.UNIQUE_INDEXES_TO_DEDUPE, mode, mode))
        for tbl, relid, cols, remap_col in cr.fetchall():
            key_expr = ", ".join(f"COALESCE(m.master_id, x.{c})" if c == remap_col else f"x.{c}" for c in cols)
            where_cl = ""
            if mode == "poly":
                cr.execute(SQL(Q.POLY_MODEL_COL, relid))
                model_col = cr.fetchone()[0]
                where_cl = f"WHERE x.{model_col} = 'res.partner'"
            cr.execute(SQL(Q.DEDUPE_ONE.format(key_expr=key_expr, tbl=tbl, remap_col=remap_col, where_cl=where_cl)))
            if cr.rowcount:
                out.append((tbl, cr.rowcount))
        return out

    def _run_merge(self, cr):
        """The whole merge, on the cursor it is given. Returns the figures."""
        res = {}
        t0 = time.time()
        res["dedupe_fk"] = self._dedupe(cr, "fk")

        n = 0
        cr.execute(Q.FK_COLUMNS_ALL)
        for tbl, col in cr.fetchall():
            cr.execute(SQL(Q.REMAP_FK.format(tbl=tbl, col=col)))
            n += cr.rowcount
        cr.execute(Q.REMAP_PARENT)
        n += cr.rowcount
        res["remapped"] = n

        # recalculated here on purpose: remapping partner_id above creates collisions
        # on res_id that did not exist at the start of the transaction
        res["dedupe_poly"] = self._dedupe(cr, "poly")

        n = 0
        cr.execute(Q.POLY_TABLES)
        for tbl, model_col in cr.fetchall():
            cr.execute(SQL(Q.REMAP_POLY.format(tbl=tbl, model_col=model_col)))
            n += cr.rowcount
        res["remapped_poly"] = n

        n = 0
        for col in Q.FILL_FIELDS:
            cr.execute(SQL(Q.FILL_ONE.format(col=col)))
            n += cr.rowcount
        res["filled"] = n

        cr.execute(Q.ARCHIVE_ABSORBED if self.archive_instead_of_delete else Q.DELETE_ABSORBED)
        res["removed"] = cr.rowcount

        leftover = []
        cr.execute(Q.POLY_TABLES)
        for tbl, model_col in cr.fetchall():
            cr.execute(
                SQL(
                    f"SELECT count(*) FROM {tbl} WHERE {model_col} = 'res.partner' "
                    "AND res_id IN (SELECT old_id FROM pm_map)"
                )
            )
            left = cr.fetchone()[0]
            if left:
                leftover.append((tbl, left))
        res["leftover"] = leftover
        res["seconds"] = time.time() - t0
        return res

    def _format(self, res, applied):
        head = self.env._("APPLIED") if applied else self.env._("SIMULATION — nothing was changed")
        lines = [
            f"=== {head} ===",
            self.env._("de-duplicated before remap : %s", res["dedupe_fk"] or self.env._("no collisions")),
            self.env._("foreign keys remapped      : %s rows", res["remapped"]),
            self.env._("de-duplicated on res_id    : %s", res["dedupe_poly"] or self.env._("no collisions")),
            self.env._("polymorphic links remapped : %s rows", res["remapped_poly"]),
            self.env._("empty fields filled in     : %s", res["filled"]),
            self.env._(
                "records %(what)s          : %(n)s",
                what=self.env._("archived") if self.archive_instead_of_delete else self.env._("deleted"),
                n=res["removed"],
            ),
            self.env._("references left behind     : %s", res["leftover"] or self.env._("none — correct")),
            self.env._("took                       : %.1f s", res["seconds"]),
        ]
        return "\n".join(lines)

    def action_simulate(self):
        """Runs everything inside a savepoint, then rolls the savepoint back.

        Not a flag that can be forgotten: the work is undone by the database, so a
        simulation cannot write even if this code is wrong.

        A savepoint on the current cursor, deliberately — NOT a second cursor. The
        working tables (pm_map & co.) are created by action_analyze in this same
        transaction, so a second cursor cannot see them and blocks waiting for the
        ACCESS EXCLUSIVE lock that CREATE TABLE holds until commit. That is a
        deadlock: the simulation waits for a transaction that only ends after the
        simulation returns.
        """
        self.ensure_one()
        if self.state not in ("analyzed", "simulated"):
            raise UserError(self.env._("Analyze the batch first."))

        class _Rollback(Exception):
            pass

        res = {}
        try:
            with self.env.cr.savepoint():
                res.update(self._run_merge(self.env.cr))
                raise _Rollback()
        except _Rollback:
            pass
        self.report = self._format(res, applied=False)
        self.state = "simulated"
        return True

    def action_apply(self):
        self.ensure_one()
        if self.state != "simulated":
            raise UserError(self.env._("Run the simulation first and read its report — then apply."))
        if not self.env.user.has_group("deltatech_partner_merge.group_partner_merge_apply"):
            raise UserError(self.env._("You are not allowed to apply a merge batch."))
        res = self._run_merge(self.env.cr)
        if res["leftover"]:
            raise UserError(
                self.env._(
                    "References were left pointing at absorbed records: %s. Rolled back — nothing applied.",
                    res["leftover"],
                )
            )
        self.report = self._format(res, applied=True)
        self.state = "done"
        _logger.info(
            "partner.merge.batch %s applied: %s records removed, %s rows remapped",
            self.id,
            res["removed"],
            res["remapped"],
        )
        return True

    def action_verify(self):
        """Compares the masters' real totals with the snapshot taken before the merge."""
        self.ensure_one()
        cr = self.env.cr
        if not self._table_exists(cr, "pm_snapshot"):
            raise UserError(self.env._("No snapshot found — analyze a batch first."))
        parts = {
            "facturi_m": "(SELECT count(*) FROM account_move mv WHERE mv.partner_id = s.master_id "
            "AND mv.move_type <> 'entry')"
            if self._table_exists(cr, "account_move")
            else "0",
            "comenzi_v_m": "(SELECT count(*) FROM sale_order so WHERE so.partner_id = s.master_id)"
            if self._table_exists(cr, "sale_order")
            else "0",
            "sold_m": "COALESCE((SELECT round(sum(l.balance)::numeric, 2) FROM account_move_line l "
            "JOIN account_account a ON a.id = l.account_id JOIN account_move mv ON mv.id = l.move_id "
            "WHERE l.partner_id = s.master_id AND mv.state = 'posted' AND a.reconcile "
            "AND NOT l.reconciled), 0)"
            if self._table_exists(cr, "account_move_line")
            else "0",
        }
        cr.execute(SQL(Q.VERIFY_TOTALS.format(**parts)))
        checked, ab_inv, ab_ord, ab_bal = cr.fetchone()
        cr.execute("SELECT count(*) FROM pm_map m JOIN res_partner p ON p.id = m.old_id")
        still = cr.fetchone()[0]
        ok = not (ab_inv or ab_ord or ab_bal) and (still == 0 or self.archive_instead_of_delete)
        self.report = "\n".join(
            [
                self.env._("=== VERIFICATION ==="),
                self.env._("masters checked            : %s", checked),
                self.env._("invoice count mismatches   : %s", ab_inv),
                self.env._("order count mismatches     : %s", ab_ord),
                self.env._("balance mismatches         : %s", ab_bal),
                self.env._("absorbed records remaining : %s", still),
                "",
                self.env._("Nothing lost, nothing duplicated.")
                if ok
                else self.env._("MISMATCHES FOUND — investigate before continuing."),
            ]
        )
        return True

    def action_reset(self):
        self.ensure_one()
        if self.state == "done":
            raise UserError(self.env._("An applied batch cannot be reset."))
        self.line_ids.unlink()
        self.write({"state": "draft", "report": False, "classification": False})
        return True

    def action_create_indexes(self):
        """Creates the missing indexes on the foreign keys towards res_partner.

        Without CONCURRENTLY, since we are inside Odoo's transaction — the lock lasts
        seconds on the big tables. Where even that is unacceptable, run
        scripts/partner_merge/01_fk_indexes.sql from psql beforehand.
        """
        self.ensure_one()
        cr = self.env.cr
        cr.execute(Q.FK_COLUMNS_WITHOUT_INDEX)
        rows = cr.fetchall()
        for tbl, col, _size in rows:
            cr.execute(SQL(f'CREATE INDEX ON {tbl} ("{col}")'))
        self.missing_index_count = 0
        self.report = self.env._("%s indexes created.", len(rows))
        return True
