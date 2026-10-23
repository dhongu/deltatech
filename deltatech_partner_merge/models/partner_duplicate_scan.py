# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

import logging
import time
from collections import defaultdict, namedtuple
from itertools import combinations

from odoo import Command, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import SQL

from . import duplicate_tools as T

_logger = logging.getLogger(__name__)

Row = namedtuple(
    "Row",
    "id name email phone vat street city zip country company_id parent_id type commercial_id has_user",
)

LOAD_PARTNERS = """
SELECT p.id, p.name, p.email, p.phone, p.vat, p.street, p.city, p.zip, c.code,
       p.company_id, p.parent_id, p.type, p.commercial_partner_id,
       EXISTS (SELECT 1 FROM res_users u WHERE u.partner_id = p.id) AS has_user
  FROM res_partner p
  LEFT JOIN res_country c ON c.id = p.country_id
 WHERE p.active
   AND ({scope})
   AND NOT EXISTS (SELECT 1 FROM res_users u WHERE u.partner_id = p.id AND NOT u.share)
   AND p.commercial_partner_id NOT IN (SELECT partner_id FROM res_company)
   {individuals}
"""

# how much one exact match weighs in the group score
KEY_SCORE = {"vat": 100, "email": 100, "phone": 95}
# above this, the fallback engine and rapidfuzz alike stop: a block that big is not a block
RAPIDFUZZ_MAX_BLOCK = 50000


class PartnerDuplicateScan(models.Model):
    _name = "partner.duplicate.scan"
    _description = "Search for probably duplicated partners"
    _order = "id desc"

    name = fields.Char(required=True, default=lambda self: self.env._("Duplicate scan"))
    state = fields.Selection([("draft", "Draft"), ("done", "Scanned")], default="draft", readonly=True, copy=False)
    use_vat = fields.Boolean(string="Same VAT", default=True)
    use_phone = fields.Boolean(string="Same phone", default=True)
    use_email = fields.Boolean(string="Same email", default=True)
    use_name = fields.Boolean(string="Similar name", default=True)
    name_match = fields.Selection(
        [("address", "Similar name and same street or postcode"), ("name", "Similar name only")],
        default="address",
        required=True,
        help="Similar names alone give many false pairs on common names (two different "
        "people called Ion Popescu in the same city). Keep the address condition unless the "
        "addresses are mostly empty.",
    )
    threshold = fields.Integer(
        string="Name similarity (%)",
        default=90,
        required=True,
        help="Minimum similarity of the normalized names (words sorted, without diacritics and "
        "legal forms), from 0 to 100.",
    )
    block_by = fields.Selection(
        [("city", "City"), ("prefix", "First letters of the name")],
        string="Compare names within",
        default="city",
        required=True,
        help="Names are only compared inside the same block, so the scan does not compare every "
        "partner with every other one. Partners without a city are blocked on the first "
        "letters of the name.",
    )
    individuals_only = fields.Boolean(string="Individuals only", help="Leave out the companies.")
    max_key_size = fields.Integer(
        string="Largest group on one value",
        default=10,
        help="A phone, email or VAT shared by more partners than this is skipped and listed in the "
        "report: it is usually a placeholder or a shared switchboard, not a duplicate.",
    )
    group_ids = fields.One2many("partner.duplicate.group", "scan_id", string="Groups")
    group_count = fields.Integer(compute="_compute_group_count")
    partner_count = fields.Integer(string="Partners scanned", readonly=True)
    engine = fields.Char(readonly=True, help="Library used for the name comparison.")
    date_scan = fields.Datetime(string="Scanned on", readonly=True)
    report = fields.Text(readonly=True)

    @api.depends("group_ids")
    def _compute_group_count(self):
        for scan in self:
            scan.group_count = len(scan.group_ids)

    @api.constrains("threshold", "max_key_size")
    def _check_limits(self):
        for scan in self:
            if not 50 <= scan.threshold <= 100:
                raise UserError(self.env._("The name similarity must be between 50 and 100."))
            if scan.max_key_size < 2:
                raise UserError(self.env._("The largest group on one value must be at least 2."))

    # ------------------------------------------------------------------ loading

    def _load_partners(self):
        scope, company_ids = self.env["partner.merge.batch"]._partner_scope()
        query = LOAD_PARTNERS.format(
            scope=scope.replace("company_id", "p.company_id"),
            individuals="AND NOT p.is_company" if self.individuals_only else "",
        )
        self.env.flush_all()
        self.env.cr.execute(SQL(query, company_ids))
        return [Row(*row) for row in self.env.cr.fetchall()]

    def _load_ignored(self):
        self.env.cr.execute("SELECT partner_a_id, partner_b_id FROM partner_duplicate_ignore")
        return set(self.env.cr.fetchall())

    # ------------------------------------------------------------------ matching

    def _find_groups(self, rows):
        """Returns ([(member ids, {(a, b): {reason: score}}, has an exact match)], report lines).

        Every pair found is an edge; the groups are the connected components, so a partner with
        the phone of A and the email of B brings A and B into the same group."""
        info = {row.id: row for row in rows}
        ignored = self._load_ignored()
        default_country = self.env.company.country_id.code
        union = T.UnionFind()
        edges = defaultdict(dict)
        exact_pairs = set()
        report = []

        def ancestors(partner_id):
            seen = set()
            parent = info[partner_id].parent_id
            while parent and parent not in seen:
                seen.add(parent)
                parent = info[parent].parent_id if parent in info else None
            return seen

        def allowed(a, b):
            row_a, row_b = info[a], info[b]
            if row_a.company_id != row_b.company_id or (a, b) in ignored:
                return False
            # refused by the standard merge wizard
            if row_a.has_user and row_b.has_user:
                return False
            if a in ancestors(b) or b in ancestors(a):
                return False
            # invoice and delivery addresses of the same customer share its phone and email
            return not (row_a.parent_id and row_a.parent_id == row_b.parent_id and row_a.type != row_b.type)

        def add_edge(a, b, reason, score, exact=False):
            a, b = min(a, b), max(a, b)
            if allowed(a, b):
                edges[(a, b)][reason] = max(score, edges[(a, b)].get(reason, 0))
                if exact:
                    exact_pairs.add((a, b))
                union.union(a, b)

        # (code, label, value shown in the reason, comparison key of that value)
        keys = []
        if self.use_vat:
            # the contacts of a company carry its VAT: only the commercial entity counts
            keys.append(
                (
                    "vat",
                    self.env._("same VAT"),
                    lambda r: r.id == r.commercial_id and T.normalize_vat(r.vat),
                    lambda value: value,
                )
            )
        if self.use_email:
            keys.append(("email", self.env._("same email"), lambda r: T.normalize_email(r.email), lambda value: value))
        if self.use_phone:
            keys.append(
                (
                    "phone",
                    self.env._("same phone"),
                    lambda r: T.normalize_phone(r.phone, r.country or default_country),
                    T.phone_key,
                )
            )
        for code, label, normalize, key_of in keys:
            buckets = defaultdict(list)
            shown = {}
            for row in rows:
                value = normalize(row)
                if value:
                    bucket = (row.company_id, key_of(value))
                    buckets[bucket].append(row.id)
                    shown.setdefault(bucket, value.lstrip("~"))
            for bucket, ids in buckets.items():
                if len(ids) < 2:
                    continue
                if len(ids) > self.max_key_size:
                    report.append(
                        self.env._(
                            "%(count)s partners with %(label)s %(value)s: skipped",
                            label=label,
                            value=shown[bucket],
                            count=len(ids),
                        )
                    )
                    continue
                for a, b in combinations(ids, 2):
                    add_edge(a, b, f"{label} {shown[bucket]}", KEY_SCORE[code], exact=True)

        if self.use_name:
            report += self._match_names(rows, add_edge)
        groups = []
        for members in union.groups():
            pairs = [pair for pair in combinations(members, 2) if pair in edges]
            groups.append((members, {pair: edges[pair] for pair in pairs}, bool(exact_pairs.intersection(pairs))))
        return groups, report

    def _match_names(self, rows, add_edge):
        blocks = defaultdict(list)
        for row in rows:
            name = T.normalize_name(row.name)
            if not name:
                continue
            city = T.normalize_city(row.city) if self.block_by == "city" else ""
            block = city or "#" + T.name_prefix(row.name)
            blocks[(row.company_id, block)].append(
                (row, name, T.normalize_street(row.street), (row.zip or "").replace(" ", ""))
            )
        report = []
        for (_company, block), members in blocks.items():
            limit = RAPIDFUZZ_MAX_BLOCK if T.has_rapidfuzz() else T.DIFFLIB_MAX_BLOCK
            if len(members) > limit:
                report.append(
                    self.env._(
                        "Names not compared in block %(block)s: %(count)s partners", block=block, count=len(members)
                    )
                )
                continue
            pairs = T.similar_pairs([member[1] for member in members], self.threshold)
            for i, j, score in pairs or []:
                row_a, _name_a, street_a, zip_a = members[i]
                row_b, _name_b, street_b, zip_b = members[j]
                if street_a and street_a == street_b:
                    reason = self.env._("name %s%% + same street", score)
                elif self.name_match == "name":
                    reason = self.env._("name %s%%", score)
                elif zip_a and zip_a == zip_b:
                    reason = self.env._("name %s%% + same postcode", score)
                else:
                    continue
                add_edge(row_a.id, row_b.id, reason, score)
        return report

    # ------------------------------------------------------------------ actions

    def action_scan(self):
        self.ensure_one()
        self.env["partner.duplicate.group"].check_access("create")
        started = time.monotonic()
        rows = self._load_partners()
        groups, report = self._find_groups(rows)
        self.group_ids.unlink()
        companies = {row.id: row.company_id for row in rows}
        vals_list = []
        for members, edges, exact in groups:
            reasons = sorted({reason for found in edges.values() for reason in found})
            vals_list.append(
                {
                    "scan_id": self.id,
                    "company_id": companies[members[0]],
                    "partner_ids": [Command.set(members)],
                    "score": max(score for found in edges.values() for score in found.values()),
                    "reasons": "\n".join(reasons),
                    "match_type": "exact" if exact else "fuzzy",
                }
            )
        self.env["partner.duplicate.group"].create(vals_list)
        engine = "rapidfuzz" if T.has_rapidfuzz() else "difflib"
        elapsed = time.monotonic() - started
        header = [
            self.env._("Partners scanned: %s", len(rows)),
            self.env._("Groups found: %s", len(vals_list)),
            self.env._("Name comparison: %s", engine),
            self.env._("Duration: %.1f s", elapsed),
        ]
        if engine == "difflib":
            header.append(
                self.env._(
                    "rapidfuzz is not installed: names are compared with difflib, only in blocks of at "
                    "most %s partners. Install rapidfuzz for large databases.",
                    T.DIFFLIB_MAX_BLOCK,
                )
            )
        self.write(
            {
                "state": "done",
                "partner_count": len(rows),
                "engine": engine,
                "date_scan": fields.Datetime.now(),
                "report": "\n".join(header + [""] + report),
            }
        )
        _logger.info("Duplicate scan %s: %s partners, %s groups in %.1fs", self.id, len(rows), len(vals_list), elapsed)
        return True

    def action_refresh(self):
        self.group_ids._refresh_state()
        return True

    def action_reset(self):
        self.group_ids.unlink()
        self.write({"state": "draft", "report": False, "partner_count": 0})
        return True
