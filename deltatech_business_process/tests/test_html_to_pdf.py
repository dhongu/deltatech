# © 2026 Deltatech
# See README.rst file on addons root folder for license details

import subprocess
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase

from odoo.addons.deltatech_business_process.tools import html_to_pdf as h2p

HTML = "<!DOCTYPE html><html><body><h1>Sheet</h1></body></html>"


class TestHtmlToPdf(TransactionCase):
    def test_empty_html_returns_none(self):
        self.assertIsNone(h2p.html_to_pdf(None))
        self.assertIsNone(h2p.html_to_pdf(""))

    def test_missing_wkhtmltopdf_returns_none(self):
        with patch("odoo.tools.find_in_path", side_effect=OSError("not found")):
            self.assertIsNone(h2p.html_to_pdf(HTML))

    def test_conversion_failure_returns_none(self):
        def fail_run(cmd, **kwargs):
            raise subprocess.CalledProcessError(1, cmd)

        with (
            patch("odoo.tools.find_in_path", return_value="/bin/wkhtmltopdf"),
            patch.object(h2p.subprocess, "run", side_effect=fail_run),
        ):
            self.assertIsNone(h2p.html_to_pdf(HTML))

    def test_missing_output_file_returns_none(self):
        # the conversion "succeeds" but produces no output file
        with (
            patch("odoo.tools.find_in_path", return_value="/bin/wkhtmltopdf"),
            patch.object(h2p.subprocess, "run", return_value=MagicMock(returncode=0)),
        ):
            self.assertIsNone(h2p.html_to_pdf(HTML))

    def test_successful_conversion_returns_bytes(self):
        def fake_run(cmd, **kwargs):
            out_pdf = cmd[-1]
            with open(out_pdf, "wb") as fh:
                fh.write(b"%PDF-1.4 fake")
            return MagicMock(returncode=0)

        with (
            patch("odoo.tools.find_in_path", return_value="/bin/wkhtmltopdf"),
            patch.object(h2p.subprocess, "run", side_effect=fake_run),
        ):
            pdf = h2p.html_to_pdf(HTML)
        self.assertEqual(pdf, b"%PDF-1.4 fake")

    def test_real_wkhtmltopdf_if_available(self):
        try:
            from odoo.tools import find_in_path  # noqa: PLC0415

            find_in_path("wkhtmltopdf")
        except (ImportError, OSError):
            self.skipTest("wkhtmltopdf not installed")
        pdf = h2p.html_to_pdf(HTML)
        self.assertTrue(pdf)
        self.assertTrue(pdf.startswith(b"%PDF"))
