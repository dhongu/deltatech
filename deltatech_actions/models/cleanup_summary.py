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
    requeue a method inside the same run, so a large backlog is cleared over
    consecutive batches instead of one per day.

    Two things guard the autovacuum job itself, and they are not optional.

    ``_run_vacuum_cleaner`` reports progress as ``_commit_progress()`` -- with no
    arguments, so ``processed`` is 0 and the cron's ``done`` counter stays at
    zero no matter how much work the vacuum methods did. Meanwhile
    ``ir.cron._process_job`` treats a job as failed when
    ``timed_out_counter >= CONSECUTIVE_TIMEOUT_FOR_FAILURE and not job['done']``,
    and ``_update_failure_count`` deactivates a cron that failed 5 times over 7
    days. A cleanup with a large backlog is exactly what pushes the job over its
    time limit, run after run -- so left alone it could get Odoo's own
    autovacuum switched off, taking ``_gc_file_store`` and every other core
    vacuum with it. Reporting the real count keeps ``done`` non-zero, which
    makes that verdict impossible.

    And the requeue only happens while there is comfortably time for another
    batch of the same size, measured on the batch just done, so the method stops
    asking for more work instead of being cut off mid-run.
    """
    import time  # noqa: PLC0415 -- keep this module importable without Odoo

    from odoo.tools import str2bool  # noqa: PLC0415 -- avoids an import cycle at module load

    icp = model.env["ir.config_parameter"].sudo()
    if not str2bool(icp.get_param("deltatech_actions.autovacuum_enabled", "False")):
        return None
    limit = int(icp.get_param(limit_param, 5000))

    start = time.monotonic()
    summary = getattr(model, from_settings)() or {}
    elapsed = time.monotonic() - start
    count = summary.get("count") or 0

    # Report the batch on the cron (see the docstring: this is what keeps the
    # autovacuum job from being deactivated) and read how long the run has left.
    # Only when actually running inside a cron: outside one there is no progress
    # record and no time limit, and _commit_progress() would commit the caller's
    # transaction -- surprising from a shell, and forbidden in a test.
    if model.env.context.get("ir_cron_progress_id"):
        time_left = model.env["ir.cron"]._commit_progress(count)
    else:
        time_left = float("inf")

    # A dry run selects the same rows on every call, so it must never ask to be
    # requeued -- the autovacuum job would spin on it until the cron ran out of
    # time, starving the other vacuum methods.
    remaining = bool(
        count >= limit
        and not summary.get("dry_run")
        # Half again the time this batch took: enough headroom that the next one
        # finishes inside the run rather than being killed partway.
        and time_left > elapsed * 1.5
    )
    return count, remaining
