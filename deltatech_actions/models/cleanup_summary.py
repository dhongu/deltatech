# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

# The cleanup crons share one result shape, so the settings screen can report what
# a run did (or, in dry run, what it would have done) without knowing which cleanup
# it just triggered.


def rows_summary(rows, dry_run):
    """Summarize the (id, file_size) rows selected by a PDF/label cleanup."""
    rows = rows or []
    return {
        "count": len(rows),
        "size": sum((row[1] or 0) for row in rows),
        "dry_run": dry_run,
    }


def log_prefix(dry_run):
    """'[DRY RUN] Would delete' vs 'Deleted', so a dry run never claims a deletion."""
    return "[DRY RUN] Would delete" if dry_run else "Deleted"


def autovacuum_run(model, from_settings, limit_param):
    """Shared body of the ``@api.autovacuum`` hooks.

    Why the cleanups are reachable from the autovacuum job at all: a neutralized
    database (``odoo-bin neutralize``, and every staging build restored on
    odoo.sh) has *every* cron switched off by ``base/data/neutralize.sql`` --
    except ``base.autovacuum_job``, which is explicitly spared. Another module's
    ``neutralize.sql`` cannot switch a cron back on either, because
    ``neutralize_database()`` iterates the installed modules in the arbitrary
    order Postgres returns them, so ``base``'s blanket disable may well run last
    and undo it. Hanging the cleanup off the autovacuum job is the only
    order-independent way to have a restored copy tidy itself up.

    Off by default: it only runs where ``deltatech_actions.autovacuum_enabled``
    is set, which is what a staging database does in its own neutralize.sql.

    Returns ``(done, remaining)`` -- the shape ``_run_vacuum_cleaner`` uses to
    requeue a method inside the same run, so a large backlog is cleared in one
    pass instead of one batch per day, within the cron's own time budget.
    """
    from odoo.tools import str2bool  # noqa: PLC0415 -- avoids an import cycle at module load

    icp = model.env["ir.config_parameter"].sudo()
    if not str2bool(icp.get_param("deltatech_actions.autovacuum_enabled", "False")):
        return None
    limit = int(icp.get_param(limit_param, 5000))
    summary = getattr(model, from_settings)() or {}
    count = summary.get("count") or 0
    # A dry run selects the same rows on every call, so it must never ask to be
    # requeued -- the autovacuum job would spin on it until the cron runs out of
    # time, starving the other vacuum methods.
    remaining = bool(count >= limit and not summary.get("dry_run"))
    return count, remaining
