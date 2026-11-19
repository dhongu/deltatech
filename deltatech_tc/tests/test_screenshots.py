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

        # agentul Terrabit Connect PostgreSQL: stație proprie, interogări instalate, un lanț de pagini
        cls.pg_station = Station.create({"name": "Server ERP", "company_id": company.id})
        cls.pg_station._touch(
            {
                "version": "0.1.0",
                "os": "windows",
                "agent": "tc-postgresql",
                "features": ["postgresql", "pg:erp"],
                "pg_profiles": {"erp": ["articles", "offers_since", "orders_since"]},
            }
        )
        rows = [
            {"code": "ALU-4512", "name": "Profil toc 70 mm", "price": "41.2500"},
            {"code": "ALU-4518", "name": "Profil cercevea 70 mm", "price": "38.9000"},
            {"code": "ALU-4520", "name": "Baghetă geam 24 mm", "price": "6.1500"},
        ]
        pages = []
        for page, (after, state) in enumerate(((None, "done"), ("ALU-4508", "done"), ("ALU-4520", "pending"))):
            job = Job._tc_enqueue_pg_query(
                cls.pg_station, "erp", "articles", params={"year": 2026}, page_size=3, after=after, page=page
            )
            pages.append(job)
            if state == "done":
                job.write(
                    {
                        "state": "done",
                        "attempt_count": 1,
                        "claimed_at": now - timedelta(seconds=30 - page * 10),
                        "done_at": now - timedelta(seconds=29 - page * 10),
                        "result": json.dumps(
                            {
                                "columns": [
                                    {"name": "code", "type": "varchar"},
                                    {"name": "name", "type": "text"},
                                    {"name": "price", "type": "numeric"},
                                ],
                                "rows": rows,
                                "count": 3,
                                "more": True,
                                "next": rows[-1]["code"],
                                "page": page,
                                "elapsed_ms": 38,
                            },
                            ensure_ascii=False,
                            indent=1,
                        ),
                    }
                )
        cls.pg_page = pages[1]

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
            # 6. o pagină de interogare PostgreSQL: parametrii (pagina, after) și rândurile primite
            {
                "url": f"action={act_job}&id={self.pg_page.id}&model=deltatech.tc.job&view_type=form",
                "name": "06_pg_query_pagina.png",
                "wait": ".o_form_view",
                "click_tab": {"ro_RO": "Rezultat", "en_US": "Result"},
                "highlight": ["div[name='job_type']", ".o_notebook .tab-pane.active"],
                "settle": 1500,
            },
            # 7. stația agentului PostgreSQL: Agent și interogările instalate
            {
                "url": f"action={act_station}&id={self.pg_station.id}&model=deltatech.tc.station&view_type=form",
                "name": "07_statie_postgresql.png",
                "eval": _pad_values("agent_name", "capabilities_display"),
                "wait": ".o_form_view",
                "highlight": ["div[name='agent_name']", "div[name='capabilities_display']"],
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
