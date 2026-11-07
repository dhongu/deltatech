# © 2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturile fișei consultant „Stații Terrabit Connect": RO pentru fișă, EN pentru USAGE.md.
#
# Seedează: o stație reală (driver fiscalwire), o stație simulată (casa de marcat și un terminal de
# card simulate, raportate prin heartbeat) și câteva joburi în toate stările cozii.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_tc,l10n_ro_doc_screenshots \
#       --test-tags=/deltatech_tc:TestTcScreenshots --stop-after-init
import json
import unittest
from datetime import timedelta

from odoo import fields
from odoo.tests import tagged

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


def _pad_values(*names):
    """JS care împinge spre dreapta valorile evidențiate, de sub badge-ul numerotat."""
    selector = ", ".join(f"div[name='{name}']" for name in names)
    return f'document.querySelectorAll("{selector}").forEach((el) => {{ el.style.paddingLeft = "18px"; }});'


@tagged("-at_install", "post_install", "fise_screenshots")
class TestTcScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_tc"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        company = cls.prepare_ro_company(name="Demo Magazin SRL")
        env = cls.env
        Station = env["deltatech.tc.station"]
        Station.search([]).write({"active": False})
        cls.station = Station.create({"name": "PC Contabilitate", "company_id": company.id})
        cls.station._touch(
            {
                "version": "1.8.2",
                "os": "Windows 11",
                "features": ["anaf", "fiscal", "zebra"],
                "fiscal_driver": "fiscalwire",
                "simulated": [],
            }
        )
        cls.station.note = "Birou contabilitate, etaj 1. Responsabil: Ana Popescu."
        cls.simulated = Station.create({"name": "Casa 1 Magazin (test)", "company_id": company.id})
        cls.simulated._touch(
            {
                "version": "1.8.2",
                "os": "Windows 11",
                "features": ["fiscal", "terminal"],
                "fiscal_driver": "simulated",
                "simulated": ["fiscal", "terminal:demo"],
            }
        )

        Job = env["deltatech.tc.job"]
        now = fields.Datetime.now()
        Job.create({"station_id": cls.station.id, "company_id": company.id, "job_type": "ping"}).write(
            {"state": "done", "claimed_at": now - timedelta(minutes=5), "done_at": now - timedelta(minutes=5)}
        )
        Job.create(
            {
                "station_id": cls.station.id,
                "company_id": company.id,
                "job_type": "http_request",
                "payload": json.dumps({"url": "http://192.168.1.50/api/Lines/1/Lots", "method": "POST"}),
            }
        ).write({"state": "claimed", "claimed_at": now - timedelta(minutes=3), "attempt_count": 1})
        cls.error_job = Job.create(
            {
                "station_id": cls.station.id,
                "company_id": company.id,
                "job_type": "http_request",
                "payload": json.dumps({"url": "http://192.168.1.60/status", "method": "GET"}),
            }
        )
        cls.error_job.write(
            {
                "state": "error",
                "claimed_at": now - timedelta(minutes=2),
                "done_at": now - timedelta(minutes=2),
                "attempt_count": 1,
                "error": "host 192.168.1.60 is not in TERRABIT_HTTP_ALLOW",
            }
        )
        Job.create({"station_id": cls.simulated.id, "company_id": company.id, "job_type": "ping"})

    def _shots(self):
        env = self.env
        act_station = env.ref("deltatech_tc.action_deltatech_tc_station").id
        act_job = env.ref("deltatech_tc.action_deltatech_tc_job").id
        return [
            # 1. lista stațiilor: stația simulată e evidențiată
            {
                "url": f"action={act_station}&view_type=list",
                "name": "01_lista_statii.png",
                "wait": ".o_list_view",
                "settle": 1500,
            },
            # 2. stația reală: butoanele din antet și datele raportate la heartbeat
            {
                "url": f"action={act_station}&id={self.station.id}&model=deltatech.tc.station&view_type=form",
                "name": "02_formular_statie.png",
                # badge-ul numerotat stă pe colțul stânga-sus: valoarea se împinge spre dreapta
                "eval": _pad_values("last_seen", "fiscal_driver"),
                "wait": ".o_form_view",
                "highlight": [
                    "button[name='action_ping']",
                    "button[name='action_download_config']",
                    "div[name='last_seen']",
                    "div[name='fiscal_driver']",
                ],
                "settle": 1500,
            },
            # 3. stația simulată: panglica Simulare și avertismentul
            {
                "url": f"action={act_station}&id={self.simulated.id}&model=deltatech.tc.station&view_type=form",
                "name": "03_statie_simulata.png",
                # badge-ul numerotat stă pe colțul stânga-sus: valoarea se împinge spre dreapta
                "eval": _pad_values("fiscal_driver"),
                "wait": ".o_form_view",
                "highlight": [".o_form_sheet .alert-warning", "div[name='fiscal_driver']"],
                "settle": 1500,
            },
            # 4. coada de joburi, în toate stările
            {
                "url": f"action={act_job}&view_type=list",
                "name": "04_lista_joburi.png",
                "wait": ".o_list_view",
                "settle": 1500,
            },
            # 5. un job în eroare: tab-ul Eroare și butonul Reîncearcă
            {
                "url": f"action={act_job}&id={self.error_job.id}&model=deltatech.tc.job&view_type=form",
                "name": "05_job_eroare.png",
                "wait": ".o_form_view",
                "click_tab": {"ro_RO": "Eroare", "en_US": "Error"},
                "highlight": ["button[name='action_retry']"],
                "settle": 1500,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), hide_systray=True, viewport=(1400, 900))

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), hide_systray=True, viewport=(1400, 900), lang="en_US")
