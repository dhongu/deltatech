# © 2026 Deltatech
# See README.rst file on addons root folder for license details


def code_display_name(record, *extra_codes):
    """Display name ``[code] name`` shared by the business models with a code.

    With ``formatted_display_name`` in the context (many2one dropdown) the code goes in
    a second, muted column: ``name\\t--code · extra--``; empty parts are left out.
    """
    if record.env.context.get("formatted_display_name"):
        codes = " · ".join(code for code in (record.code, *extra_codes) if code)
        return f"{record.name}\t--{codes}--" if codes else f"{record.name}"
    return "{}{}".format(record.code and f"[{record.code}] " or "", record.name)
