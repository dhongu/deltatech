# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Foi de parcurs, alimentări și carduri de combustibil", în RO
# (fișa) și EN (readme/USAGE.md).
#
# Seedează un vehicul cu card și carburant, trei locații cu trasee, o alimentare și o foaie
# de parcurs din 5 octombrie 2026 (luni), cu trei trasee și alimentarea legată. Al doilea
# vehicul are doar citiri de kilometraj și o alimentare, ca raportul costului pe kilometru
# să aibă două rânduri. Raportul se calculează în seed, pe octombrie 2026, iar captura
# deschide lista lui.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_fleet,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest
from datetime import datetime, timedelta

from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# 5 octombrie 2026, luni. Browserul capturilor rulează în UTC, deci și utilizatorul, ca orele
# din formular și din PDF să fie aceleași.
DAY = datetime(2026, 10, 5)

# bulinele numerotate ale evidențierilor stau pe colțul celulei; tabelul le-ar tăia
# (stil injectat, nu pe noduri: fila Fuel Logs se randează abia după click)
SHOW_BADGES_JS = (
    "const style = document.createElement('style'); "
    "style.textContent = '.o_list_renderer, .table-responsive, .o_list_table td { overflow: visible !important; }'; "
    "document.head.appendChild(style);"
)
SCROLL_TO_NOTEBOOK_JS = "document.querySelector('.o_notebook').scrollIntoView({block: 'start'}); " + SHOW_BADGES_JS

# perioada raportului costului pe kilometru, în formatul de dată al limbii
PERIOD = {"ro_RO": ("01.10.2026", "31.10.2026"), "en_US": ("10/01/2026", "10/31/2026")}
# câmpul de dată e un buton până la click; după fiecare dată închidem selectorul rămas
# deschis, altfel click-ul pe câmpul următor doar îl închide pe primul
SET_PERIOD_JS = """(async () => {
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    for (const [name, value] of [["date_from", "%s"], ["date_to", "%s"]]) {
        document.querySelector(`.modal div[name='${name}'] button, .modal div[name='${name}'] input`).click();
        await sleep(400);
        const input = document.querySelector(`.modal div[name='${name}'] input`);
        input.value = value;
        input.dispatchEvent(new Event("input", {bubbles: true}));
        input.dispatchEvent(new Event("change", {bubbles: true}));
        input.dispatchEvent(new KeyboardEvent("keydown", {key: "Enter", bubbles: true}));
        await sleep(400);
        if (document.querySelector(".o_datetime_picker")) {
            // Escape fără selector deschis ar închide fereastra
            document.body.dispatchEvent(new KeyboardEvent("keydown", {key: "Escape", bubbles: true}));
            await sleep(400);
        }
    }
})()"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestFleetScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_fleet"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company()
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"tz": "UTC", "group_ids": [(4, env.ref("fleet.fleet_group_manager").id)]})

        brand = env["fleet.vehicle.model.brand"].create({"name": "Dacia"})
        logan = env["fleet.vehicle.model"].create({"name": "Logan", "brand_id": brand.id})
        duster = env["fleet.vehicle.model"].create({"name": "Duster", "brand_id": brand.id})
        driver = env["res.partner"].create({"name": "Andrei Ionescu"})
        driver2 = env["res.partner"].create({"name": "Mihai Stan"})
        cls.diesel = env["fleet.fuel"].create({"name": "Motorină", "fuel_type": "diesel"})
        cls.card = env["fleet.card"].create({"name": "7080 1234 5678"})
        cls.vehicle = env["fleet.vehicle"].create(
            {
                "model_id": logan.id,
                "license_plate": "B-101-TRB",
                "driver_id": driver.id,
                "driver2_id": driver2.id,
                "vehicle_category_id": env.ref("deltatech_fleet.id_category_M1").id,
                "reservoir": 50,
                "avg_cons": 6.5,
                "card_ids": [(6, 0, cls.card.ids)],
            }
        )
        vehicle2 = env["fleet.vehicle"].create(
            {
                "model_id": duster.id,
                "license_plate": "B-202-TRB",
                "vehicle_category_id": env.ref("deltatech_fleet.id_category_M1").id,
                "avg_cons": 7.5,
            }
        )

        bucuresti = env["fleet.location"].create({"name": "București - sediu"})
        ploiesti = env["fleet.location"].create({"name": "Ploiești - client", "type": "1"})
        pitesti = env["fleet.location"].create({"name": "Pitești - depozit", "type": "1"})
        to_ploiesti = env["fleet.route"].create(
            {"from_loc_id": bucuresti.id, "to_loc_id": ploiesti.id, "distance": 60, "duration": 1.0, "dist_c1": 60}
        )
        to_ploiesti.button_create_reverse()
        to_pitesti = env["fleet.route"].create(
            {"from_loc_id": bucuresti.id, "to_loc_id": pitesti.id, "distance": 120, "duration": 1.75, "dist_c1": 120}
        )
        scope = env["fleet.scope"].create({"name": "Livrare marfă"})

        def odometer(vehicle, value, when):
            env["fleet.vehicle.odometer"].create(
                {"vehicle_id": vehicle.id, "value": value, "date": when.date(), "date_time": when}
            )

        odometer(cls.vehicle, 45000, datetime(2026, 9, 30, 15))
        odometer(vehicle2, 120000, datetime(2026, 9, 30, 15))
        odometer(vehicle2, 121500, datetime(2026, 10, 31, 15))
        # citirea de la sfârșitul lunii: vehiculul nu a mai circulat după foaia din 5 octombrie
        odometer(cls.vehicle, 45240, datetime(2026, 10, 31, 15))

        fuel_service = env.ref("deltatech_fleet.type_service_service_fuel")
        # alimentarea anterioară dă nivelul rezervorului la începutul foii
        env["fleet.vehicle.log.fuel"].create(
            {
                "vehicle_id": cls.vehicle.id,
                "service_type_id": fuel_service.id,
                "date": "2026-09-28",
                "date_time": datetime(2026, 9, 28, 9),
                "card_id": cls.card.id,
                "fuel_id": cls.diesel.id,
                "liter": 9,
                "price_per_liter": 7.1,
                "amount": 63.9,
                "odometer": 44800,
            }
        )
        cls.fuel_log = env["fleet.vehicle.log.fuel"].create(
            {
                "name": "Alimentare 5 oct.",
                "vehicle_id": cls.vehicle.id,
                "service_type_id": fuel_service.id,
                "date": DAY.date(),
                "date_time": DAY.replace(hour=7, minute=30),
                "card_id": cls.card.id,
                "fuel_id": cls.diesel.id,
                "liter": 40,
                "price_per_liter": 7.2,
                "amount": 288,
                "full": True,
                "odometer": 45000,
            }
        )
        env["fleet.vehicle.log.fuel"].create(
            {
                "vehicle_id": vehicle2.id,
                "service_type_id": fuel_service.id,
                "date": "2026-10-12",
                "date_time": datetime(2026, 10, 12, 6),
                "fuel_id": cls.diesel.id,
                "liter": 100,
                "price_per_liter": 7.3,
                "amount": 730,
                "odometer": 120400,
            }
        )

        cls.sheet = env["fleet.map.sheet"].create(
            {
                # numărul fix: secvența nu se anulează la rollback, deci ar crește la fiecare rulare
                "name": "MS/00010",
                "vehicle_id": cls.vehicle.id,
                "driver_id": driver.id,
                "driver2_id": driver2.id,
                "date": DAY.date(),
                "date_start": DAY.replace(hour=6),
                "date_end": DAY.replace(hour=18),
            }
        )
        for hour, minute, route in ((8, 0, to_ploiesti), (10, 0, to_ploiesti.reverse), (12, 30, to_pitesti)):
            begin = DAY.replace(hour=hour, minute=minute)
            env["fleet.route.log"].create(
                {
                    "vehicle_id": cls.vehicle.id,
                    "map_sheet_id": cls.sheet.id,
                    "route_id": route.id,
                    "scope_id": scope.id,
                    "distance": route.distance,
                    "dist_c1": route.dist_c1,
                    "date_begin": begin,
                    "date_end": begin + timedelta(hours=route.duration),
                }
            )
        cls.fuel_log.map_sheet_id = cls.sheet
        cls.sheet.odometer_end = 45240

        cls.report = env["fleet.distance.report"].create({"date_from": "2026-10-01", "date_to": "2026-10-31"})
        env.flush_all()
        cls.report.do_compute()
        env.flush_all()

        cls.fuel_action = env.ref("deltatech_fleet.fleet_vehicle_log_fuel_action").id
        cls.sheet_action = env.ref("deltatech_fleet.fleet_map_sheet_act").id
        cls.report_action = env.ref("deltatech_fleet.action_fleet_distance_report").id
        cls.report_line_action = env.ref("deltatech_fleet.action_fleet_distance_report_line").id

    def _sheet_url(self):
        return f"action={self.sheet_action}&id={self.sheet.id}&model=fleet.map.sheet&view_type=form"

    def _shots(self):
        return [
            {
                "url": f"action={self.fuel_action}&id={self.fuel_log.id}&model=fleet.vehicle.log.fuel&view_type=form",
                "name": "01_alimentare.png",
                "wait": ".o_form_view div[name='liter']",
                "highlight": [
                    "div[name='date_time']",
                    "div[name='liter']",
                    "div[name='map_sheet_id']",
                    "div[name='odometer']",
                ],
            },
            {
                "url": self._sheet_url(),
                "name": "02_foaie_parcurs.png",
                "wait": ".o_form_view div[name='odometer_start']",
                "highlight": [
                    "div[name='vehicle_id']",
                    "div[name='date_start']",
                    "div[name='date_end']",
                    "div.o_row:has(div[name='odometer_start'])",
                    "div.o_row:has(div[name='odometer_end'])",
                ],
            },
            {
                "url": self._sheet_url(),
                "name": "03_traseu_parcurs.png",
                "wait": ".o_form_view div[name='route_log_ids'] .o_data_row",
                "eval": SCROLL_TO_NOTEBOOK_JS,
                "highlight": [
                    "button[name='action_get_route_log']",
                    "div[name='route_log_ids'] .o_data_row:first-child td[name='route_id']",
                    "div[name='route_log_ids'] .o_data_row:first-child td[name='distance']",
                ],
            },
            {
                "url": self._sheet_url(),
                "name": "04_alimentari_foaie.png",
                "wait": ".o_form_view div[name='route_log_ids']",
                "click_tab": "Fuel Logs",
                "wait_after": "div[name='log_fuel_ids'] .o_data_row",
                "eval": SCROLL_TO_NOTEBOOK_JS,
                "highlight": [
                    "button[name='action_get_log_fuel']",
                    "div[name='log_fuel_ids'] .o_data_row td[name='liter']",
                    "div[name='log_fuel_ids'] .o_data_row td[name='amount']",
                ],
            },
            {
                "url": self._sheet_url(),
                "name": "05_verificare_foaie.png",
                "wait": ".o_form_view div[name='distance_total']",
                "highlight": [
                    "div[name='distance_total']",
                    "div[name='liter_total']",
                    "div[name='norm_cons']",
                    "div[name='reservoir_level_start']",
                    "div[name='reservoir_level_end']",
                ],
            },
            self.report_shot("deltatech_fleet.report_map_sheet", self.sheet, "06_foaie_parcurs_pdf.png"),
            {
                "url": self._sheet_url(),
                "name": "07_confirmare_foaie.png",
                "wait": ".o_form_view button[name='action_open']",
                "click_btn": "button[name='action_open']",
                "wait_after": "button[name='action_done']",
                "highlight": ["button[name='action_done']", ".o_statusbar_status"],
            },
            {
                "url": f"action={self.report_action}",
                "name": "08_raport_cost_km_perioada.png",
                "wait": ".modal div[name='date_from'] input",
                "eval": {lang: SET_PERIOD_JS % dates for lang, dates in PERIOD.items()},
                "highlight": [
                    ".modal div[name='date_from']",
                    ".modal div[name='date_to']",
                    ".modal button[name='button_show_report']",
                ],
            },
            {
                "url": f"action={self.report_line_action}&active_id={self.report.id}&view_type=list",
                "name": "09_raport_cost_km.png",
                "wait": ".o_list_view .o_data_row",
                "eval": SHOW_BADGES_JS,
                "highlight": [
                    ".o_data_row:first-child td[name='cost']",
                    ".o_data_row:first-child td[name='distance']",
                    ".o_data_row:first-child td[name='price']",
                ],
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots())

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), lang="en_US")
