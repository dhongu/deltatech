# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Registru SSM" — generate în timpul testelor, în limba RO
# (fișa consultant) și EN (readme/USAGE.md).
#
# Fluxul: registrul evenimentelor, un near miss, un accident cu incapacitate cu persoana
# vătămată, acțiunile corective, evenimentul închis, lista acțiunilor și indicatorii anului
# (cu LTIFR calculat și cu avertismentul pentru lunile fără pontaj).
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_safety_register,deltatech_doc_screenshots \
#       --test-tags=/deltatech_safety_register:TestSafetyRegisterScreenshots --stop-after-init
import unittest
from datetime import datetime, timedelta

from odoo import fields
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestSafetyRegisterScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_safety_register"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        company = cls.prepare_ro_company()
        cls.admin = cls.env.ref("base.user_admin")
        cls.today = fields.Date.context_today(cls.admin)
        cls.year = cls.today.year
        cls.last_year = cls.year - 1

        Employee = cls.env["hr.employee"]
        production = cls.env["hr.department"].create({"name": "Producție", "company_id": company.id})
        logistics = cls.env["hr.department"].create({"name": "Logistică", "company_id": company.id})
        cls.employees = Employee.create(
            [
                {"name": "Ion Popescu", "department_id": production.id, "company_id": company.id},
                {"name": "Maria Ionescu", "department_id": production.id, "company_id": company.id},
                {"name": "Andrei Stan", "department_id": logistics.id, "company_id": company.id},
                {"name": "Elena Dobre", "department_id": logistics.id, "company_id": company.id},
                {"name": "Mihai Georgescu", "department_id": production.id, "company_id": company.id},
            ]
        )
        cls.supervisor = cls.env["res.users"].create(
            {
                "name": "Vasile Marin",
                "login": "vasile.marin",
                "email": "vasile.marin@example.ro",
                "company_id": company.id,
                "company_ids": [(6, 0, company.ids)],
                "group_ids": [(6, 0, [cls.env.ref("deltatech_safety_register.group_safety_officer").id])],
            }
        )
        cls._seed_attendance()
        cls._seed_events()

        cls.indicator_full = cls.env["deltatech.safety.indicator"].create(
            {"company_id": company.id, "year": cls.last_year}
        )
        cls.indicator_missing = cls.env["deltatech.safety.indicator"].create(
            {"company_id": company.id, "year": cls.year}
        )

    @classmethod
    def _seed_attendance(cls):
        """Anul trecut: 20 de zile de 8 ore pe lună pentru fiecare angajat. Anul curent: o zi
        pe lună, fără martie, ca indicatorii să arate avertismentul pentru luna lipsă."""
        vals = []
        for employee in cls.employees:
            for month in range(1, 13):
                for day in range(1, 21):
                    check_in = datetime(cls.last_year, month, day, 6, 0)
                    vals.append(
                        {"employee_id": employee.id, "check_in": check_in, "check_out": check_in + timedelta(hours=8)}
                    )
            for month in range(1, cls.today.month + 1):
                if month == 3:
                    continue
                check_in = datetime(cls.year, month, 1, 6, 0)
                if check_in.date() >= cls.today:
                    continue
                vals.append(
                    {"employee_id": employee.id, "check_in": check_in, "check_out": check_in + timedelta(hours=8)}
                )
        cls.env["hr.attendance"].create(vals)

    @classmethod
    def _seed_events(cls):
        # mesajele din chatter (creare, finalizare) se scriu în limba contextului
        env = cls.env(context=dict(cls.env.context, lang="ro_RO"))
        Event = env["deltatech.safety.event"]
        Action = env["deltatech.safety.action"]
        # numerotarea pornește de la 1, ca în registrul unei firme noi
        cls.env.ref("deltatech_safety_register.sequence_safety_event").number_next = 1
        ly = cls.last_year
        ion, maria, andrei, elena, mihai = cls.employees
        near_misses = [
            ("Hala A, linia 2", "Palet instabil pe raftul de sus, observat înainte de a cădea."),
            ("Depozit, culoar 4", "Stivuitor intrat în zona pietonală fără semnal sonor."),
            ("Hala B", "Cablu de alimentare desfăcut pe calea de acces."),
            ("Atelier mecanic", "Apărătoarea polizorului lipsea la începutul schimbului."),
            ("Rampa de încărcare", "Ușa rampei a coborât cu o persoană sub ea; s-a oprit la timp."),
        ]
        for month, (location, description) in enumerate(near_misses, start=2):
            Event.create(
                {
                    "event_type": "near_miss",
                    "date": fields.Date.to_date(f"{ly}-{month:02d}-10"),
                    "location": location,
                    "description": description,
                }
            )
        Event.create(
            {
                "event_type": "incident",
                "date": fields.Date.to_date(f"{ly}-04-22"),
                "location": "Depozit, culoar 2",
                "description": "Raft lovit de stivuitor; marfă deteriorată, fără persoane vătămate.",
            }
        )
        Event.create(
            {
                "event_type": "lost_time_injury",
                "date": fields.Date.to_date(f"{ly}-06-14"),
                "location": "Hala A, linia 1",
                "employee_id": maria.id,
                "description": "Mâna prinsă în rolele benzii transportoare la curățare.",
                "root_cause": "Banda nu a fost oprită și blocată înainte de curățare.",
            }
        )
        Event.create(
            {
                "event_type": "lost_time_injury",
                "date": fields.Date.to_date(f"{ly}-09-03"),
                "location": "Str. Fabricii, la intrarea pe poartă",
                "employee_id": andrei.id,
                "is_commute": True,
                "description": "Căzut de pe bicicletă la venirea la serviciu.",
            }
        )
        cls.closed_event = Event.create(
            {
                "event_type": "lost_time_injury",
                "date": fields.Date.to_date(f"{ly}-10-21"),
                "location": "Atelier mecanic",
                "employee_id": mihai.id,
                "description": "Tăietură la antebraț de la o tablă neprotejată.",
                "root_cause": "Muchiile tablelor nu erau protejate la depozitare.",
            }
        )
        for description, user in (
            ("Protecții de muchie pe toate tablele din atelier", cls.supervisor),
            ("Instruire privind manipularea tablelor", cls.admin),
        ):
            Action.create(
                {
                    "event_id": cls.closed_event.id,
                    "description": description,
                    "user_id": user.id,
                    "deadline": fields.Date.to_date(f"{ly}-11-15"),
                }
            ).action_done()
        cls.closed_event.action_close()

        cls.near_miss = Event.create(
            {
                "event_type": "near_miss",
                "date": cls.today - timedelta(days=3),
                "location": "Hala B, zona de ambalare",
                "description": "O cutie a căzut de pe banda de ambalare lângă un operator; nu a lovit pe nimeni.",
            }
        )
        cls.injury = Event.create(
            {
                "event_type": "lost_time_injury",
                "date": cls.today - timedelta(days=10),
                "location": "Hala A, linia 3",
                "employee_id": ion.id,
                "description": "Entorsă la glezna stângă după alunecarea pe pardoseala udă de lângă mașina de spălat.",
                "root_cause": "Scurgere de apă nesemnalizată; lipsa covorașului antiderapant.",
            }
        )
        Action.create(
            {
                "event_id": cls.injury.id,
                "description": "Covoraș antiderapant și semnalizare la mașina de spălat",
                "user_id": cls.supervisor.id,
                "deadline": cls.today + timedelta(days=5),
            }
        )
        Action.create(
            {
                "event_id": cls.injury.id,
                "description": "Reparația scurgerii de apă",
                "user_id": cls.admin.id,
                "deadline": cls.today - timedelta(days=2),
            }
        ).action_done()
        Event.create(
            {
                "event_type": "injury",
                "date": cls.today - timedelta(days=40),
                "location": "Depozit",
                "partner_id": cls.env["res.partner"].create({"name": "Transport Rapid SRL"}).id,
                "injured_name": "Șofer extern",
                "description": "Zgârietură la mână la deschiderea obloanelor camionului.",
            }
        )
        # elena: fără eveniment; rămâne doar în pontaj
        assert elena

    def _shots(self):
        event_action = self.env.ref("deltatech_safety_register.action_safety_event").id
        action_action = self.env.ref("deltatech_safety_register.action_safety_action").id
        indicator_action = self.env.ref("deltatech_safety_register.action_safety_indicator").id
        menu = self.env.ref("deltatech_safety_register.menu_safety_root").id
        model = "deltatech.safety.event"
        tab_actions = {"ro_RO": "Acțiuni corective", "en_US": "Corrective actions"}

        def form(record, act=event_action, rmodel=model):
            return f"action={act}&menu_id={menu}&id={record.id}&model={rmodel}&view_type=form"

        return [
            {
                "url": f"action={event_action}&menu_id={menu}&model={model}&view_type=list",
                "name": "01_lista_evenimente.png",
                "wait": ".o_list_view",
            },
            {
                "url": form(self.near_miss),
                "name": "02_near_miss.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='event_type']", ".o_statusbar_status"],
            },
            {
                "url": form(self.injury),
                "name": "03_accident_incapacitate.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='employee_id']", "div[name='department_id']", "div[name='is_commute']"],
            },
            {
                "url": form(self.injury),
                "name": "04_actiuni_corective.png",
                "wait": ".o_form_view",
                "click_tab": tab_actions,
                "highlight": ["div[name='action_ids'] button[name='action_done']"],
                "settle": 2500,
            },
            {
                "url": form(self.injury),
                "name": "05_activitate_responsabil.png",
                "wait": ".o-mail-Activity",
                "hide_chatter": False,
                "highlight": [".o-mail-Activity"],
                "settle": 2500,
            },
            {
                "url": form(self.closed_event),
                "name": "06_eveniment_inchis.png",
                "wait": ".o_form_view",
                "click_tab": tab_actions,
                "highlight": [".o_statusbar_status", "div[name='closed_date']"],
            },
            {
                "url": f"action={action_action}&menu_id={menu}&model=deltatech.safety.action&view_type=list",
                "name": "07_lista_actiuni.png",
                "wait": ".o_list_view",
            },
            {
                "url": form(self.indicator_full, indicator_action, "deltatech.safety.indicator"),
                "name": "08_indicatori.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='ltifr']", "div[name='days_without_accident']"],
            },
            {
                "url": form(self.indicator_missing, indicator_action, "deltatech.safety.indicator"),
                "name": "09_indicatori_ore_lipsa.png",
                "wait": ".o_form_view",
                "highlight": [".alert-warning"],
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots())

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), lang="en_US")
