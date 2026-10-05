from odoo import SUPERUSER_ID, api, fields


def migrate(cr, version):
    """The register numbering restarts every year and never skips a number.

    The sequence of the older versions was one continuous, gap-allowed counter, and
    it is `noupdate`, so it is converted here. The range of the current year takes
    over the counter, so the next number continues the existing series.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    sequence = env.ref("deltatech_ledger.ledger_sequence", raise_if_not_found=False)
    if not sequence or sequence.use_date_range:
        return
    next_number = sequence.number_next_actual
    sequence.write({"implementation": "no_gap", "number_next": next_number})
    sequence.write({"use_date_range": True})
    year = fields.Date.context_today(sequence).year
    env["ir.sequence.date_range"].create(
        {
            "sequence_id": sequence.id,
            "date_from": f"{year}-01-01",
            "date_to": f"{year}-12-31",
            "number_next_actual": next_number,
        }
    )
