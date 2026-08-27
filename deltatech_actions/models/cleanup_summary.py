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
