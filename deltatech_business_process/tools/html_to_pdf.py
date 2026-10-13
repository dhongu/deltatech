# © 2026 Deltatech
# See README.rst file on addons root folder for license details
"""Convert self-contained HTML → PDF using wkhtmltopdf (the same engine as Odoo).

The PDF is natively previewable in Odoo, so it is suitable for attaching sheets to processes.
"""

import logging
import os
import subprocess
import tempfile

_logger = logging.getLogger(__name__)


def html_to_pdf(html):
    """Return PDF bytes from HTML (with base64 images), or None if wkhtmltopdf is missing/fails."""
    if not html:
        return None
    try:
        from odoo.tools import find_in_path  # noqa: PLC0415

        bin_path = find_in_path("wkhtmltopdf")
    except (ImportError, OSError):
        return None

    with tempfile.TemporaryDirectory() as tmp:
        in_html = os.path.join(tmp, "sheet.html")
        out_pdf = os.path.join(tmp, "sheet.pdf")
        with open(in_html, "w", encoding="utf-8") as fh:
            fh.write(html)
        try:
            subprocess.run(
                [
                    bin_path,
                    "--quiet",
                    "--encoding",
                    "utf-8",
                    "--margin-top",
                    "10",
                    "--margin-bottom",
                    "10",
                    "--margin-left",
                    "8",
                    "--margin-right",
                    "8",
                    in_html,
                    out_pdf,
                ],
                check=True,
                timeout=180,
                capture_output=True,
            )
        except (subprocess.SubprocessError, OSError) as exc:
            _logger.warning("PDF conversion failed: %s", exc)
            return None
        if not os.path.isfile(out_pdf):
            return None
        with open(out_pdf, "rb") as fh:
            return fh.read()
