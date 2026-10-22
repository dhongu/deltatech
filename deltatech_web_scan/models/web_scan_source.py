# Part of Terrabit. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields, models

from ..utils.scan import group_by_domain, scan_page

_logger = logging.getLogger(__name__)

SCAN_STATES = [
    ("new", "New"),
    ("ok", "OK"),
    ("suspect", "Suspect"),
    ("mismatch", "Other Product"),
    ("not_found", "Not Found"),
    ("blocked", "Blocked"),
    ("error", "Error"),
]
SCAN_SOURCES = [
    ("structured", "Structured Data"),
    ("selector", "Selectors"),
    ("heuristic", "HTML Patterns"),
    ("ai", "AI"),
]
# states that count as a failed reading: after _scan_max_errors in a row, the scheduled action skips the page
FAILED_STATES = ("not_found", "blocked", "error")


class WebScanSourceMixin(models.AbstractModel):
    """A web page read again and again: the page of a product at a competitor or at a vendor.

    The model that inherits it says how to read (``_scan_settings``, ``_scan_selectors``,
    ``_scan_get_session``), what to expect (``_scan_expected``, ``_scan_previous_price``) and what to
    write from what was found (``_scan_apply``). The mixin reads the page, checks it and keeps the state.
    """

    _name = "web.scan.source.mixin"
    _description = "Web Scan Source"
    _scan_max_errors = 5

    scan_url = fields.Char(string="Page URL")
    scan_state = fields.Selection(SCAN_STATES, string="Scan State", default="new", readonly=True, copy=False)
    scan_message = fields.Char(string="Scan Message", readonly=True, copy=False)
    scan_last_fetch = fields.Datetime(string="Last Scan", readonly=True, copy=False)
    scan_error_count = fields.Integer(
        string="Failed Scans",
        readonly=True,
        copy=False,
        help="Failed readings in a row; from the limit on, the scheduled action no longer reads the page.",
    )
    scan_source = fields.Selection(SCAN_SOURCES, string="Read From", readonly=True, copy=False)

    # ------------------------------------------------------------------ #
    #  To override                                                        #
    # ------------------------------------------------------------------ #

    def _scan_settings(self):
        """:return: how to read the page: ``user_agent``, ``respect_robots``, ``delay`` (seconds between two
        requests to the same domain), ``suspect_change_percent``, ``allow_heuristic``"""
        return {
            "user_agent": None,
            "respect_robots": True,
            "delay": 2.0,
            "suspect_change_percent": 50.0,
            "allow_heuristic": True,
        }

    def _scan_selectors(self):
        """:return: the selectors of ``extract_by_selectors`` for this page, for a site without schema.org data"""
        return []

    def _scan_expected(self):
        """:return: ``{"gtin": ..., "code": ...}`` of the product the page should show; a page that declares
        another barcode or code gets the state ``mismatch``"""
        return {}

    def _scan_previous_price(self):
        """:return: the price of the previous reading, for the check of the jump of price"""
        return None

    def _scan_get_session(self):
        """:return: a session of ``new_session``, logged in when the site asks for it; None for a new session"""
        return None

    def _scan_apply(self, outcome):
        """Write what was found; called after each reading, whatever its state"""
        return None

    def _scan_cron_domain(self):
        """:return: the domain of the pages the scheduled action reads (for example, the ones due)"""
        return []

    # ------------------------------------------------------------------ #
    #  Reading                                                            #
    # ------------------------------------------------------------------ #

    def _scan_message(self, outcome):
        """:return: the message shown to the user for the outcome of a reading"""
        state, detail = outcome.get("state"), outcome.get("detail") or ""
        sources = dict(self._fields["scan_source"]._description_selection(self.env))
        messages = {
            "ok": self.env._("Read from %(origin)s.", origin=sources.get(outcome.get("source"), "")),
            "suspect": self.env._("Price to confirm: %(detail)s", detail=detail),
            "mismatch": self.env._("The page shows another product: %(detail)s", detail=detail),
            "not_found": self.env._("No price found on the page (%(detail)s).", detail=detail),
            "blocked": self.env._(
                "The site refuses automatic reading (%(detail)s). Ask for a feed or an API instead.", detail=detail
            ),
            "error": self.env._("The page could not be read: %(detail)s", detail=detail),
        }
        return messages.get(state, detail)

    def _scan_one(self, session=None):
        self.ensure_one()
        if not self.scan_url:
            return {"state": "error", "detail": self.env._("no page URL"), "source": False}
        settings = self._scan_settings()
        try:
            return scan_page(
                self.scan_url,
                session=session or self._scan_get_session(),
                user_agent=settings.get("user_agent"),
                respect_robots=settings.get("respect_robots", True),
                delay=settings.get("delay") or 0,
                selectors=self._scan_selectors(),
                expected=self._scan_expected(),
                previous_price=self._scan_previous_price(),
                suspect_change_percent=settings.get("suspect_change_percent"),
                allow_heuristic=settings.get("allow_heuristic", True),
            )
        except Exception as e:  # noqa: BLE001 - one page in error does not stop the others
            _logger.warning("Scan of %s failed", self.scan_url, exc_info=True)
            return {"state": "error", "detail": str(e), "source": False}

    def _scan_fetch(self, session=None):
        """Read the pages, keep the state of each one and hand the outcome to ``_scan_apply``

        :return: ``{record id: outcome}``
        """
        outcomes = {}
        for record in self:
            outcome = record._scan_one(session=session)
            failed = outcome["state"] in FAILED_STATES
            record.write(
                {
                    "scan_state": outcome["state"],
                    "scan_message": record._scan_message(outcome),
                    "scan_last_fetch": fields.Datetime.now(),
                    "scan_source": outcome.get("source") or False,
                    "scan_error_count": record.scan_error_count + 1 if failed else 0,
                }
            )
            record._scan_apply(outcome)
            outcomes[record.id] = outcome
        return outcomes

    def action_scan_now(self):
        self._scan_fetch()
        return True

    def action_scan_confirm(self):
        """Accept a price marked as suspect"""
        self.filtered(lambda r: r.scan_state == "suspect").write(
            {"scan_state": "ok", "scan_message": self.env._("Price confirmed by %s.", self.env.user.name)}
        )
        return True

    # ------------------------------------------------------------------ #
    #  Scheduled action                                                   #
    # ------------------------------------------------------------------ #

    def _scan_commit_progress(self, processed, remaining):
        """:return: False when the scheduled action has no time left; outside of it, nothing is committed"""
        if not self.env.context.get("ir_cron_progress_id"):
            return True
        return self.env["ir.cron"]._commit_progress(processed, remaining=remaining) > 0

    def _scan_cron_run(self, domain=None, batch=200):
        """Read the pages due, the oldest first, the domains taken in turn so that the pause between two
        requests to the same site is spent on the other sites; stop when the scheduled action has no time left"""
        domain = (
            [("scan_url", "!=", False), ("scan_error_count", "<", self._scan_max_errors)]
            + self._scan_cron_domain()
            + (domain or [])
        )
        records = self.search(domain, order="scan_last_fetch asc nulls first, id", limit=batch)
        remaining = self.search_count(domain) - len(records)
        groups = list(group_by_domain(records, lambda r: r.scan_url).values())
        ordered = [group[i] for i in range(max(map(len, groups), default=0)) for group in groups if i < len(group)]
        processed = 0
        for record in ordered:
            record._scan_fetch()
            processed += 1
            if not self._scan_commit_progress(1, remaining + len(ordered) - processed):
                break
        return processed
