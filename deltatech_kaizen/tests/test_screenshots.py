# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Proiecte de îmbunătățire Kaizen" — generate în timpul
# testelor, pe compania „Demo Kaizen SRL" în RON: în RO pentru fișă și în EN
# (static/description/en/) pentru readme/USAGE.md.
#
# Proiectul „Rebut la linia de ștanțare 2" trece prin toate stările fluxului; între
# grupurile de capturi testul avansează proiectul, ca fiecare ecran să arate starea
# pasului din fișă. Al doilea proiect, „Opriri la linia de vopsire", rămâne în Acțiuni,
# cu o acțiune depășită.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_kaizen,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init --http-port=8987 --gevent-port=8988
import unittest
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    try:
        from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
    except ImportError:
        ScreenshotCase = None

FORM = ".o_form_view"
LIST = ".o_list_view"

# Desfășoară, unul câte unul, grupurile listei (Kaizen → Ishikawa e grupat pe categorie),
# ca să se vadă proiectul și cauza pe fiecare rând.
EXPAND_GROUPS = """
    new Promise(async (resolve) => {
        const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
        for (let i = 0; i < 12; i++) {
            const folded = [...document.querySelectorAll('.o_group_header')].find(
                (h) => !h.classList.contains('o_group_open')
            );
            if (!folded) break;
            folded.click();
            await sleep(400);
        }
        resolve();
    })
"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestKaizenScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_kaizen"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Kaizen SRL")
        env = cls.env
        user_group = env.ref("deltatech_kaizen.group_kaizen_user")
        manager_group = env.ref("deltatech_kaizen.group_kaizen_manager")
        env.ref("base.user_admin").group_ids = [(4, manager_group.id)]
        users = env["res.users"].with_context(no_reset_password=True)
        cls.andrei = users.create(
            {"name": "Andrei Ionescu", "login": "andrei.kaizen", "group_ids": [(6, 0, [manager_group.id])]}
        )
        cls.maria = users.create({"name": "Maria Pop", "login": "maria.kaizen", "group_ids": [(6, 0, [user_group.id])]})
        today = fields.Date.context_today(env["kaizen.project"])
        cls.today = today

        Project = env["kaizen.project"]
        cls.project = Project.create(
            {
                "name": "Rebut la linia de ștanțare 2",
                "loss_type": "scrap",
                "user_id": cls.andrei.id,
                "date_start": date(2026, 10, 1),
                "date_deadline": date(2026, 12, 31),
                "baseline_date": date(2026, 9, 30),
                "baseline_value": 12000.0,
                "target_value": 4000.0,
            }
        )
        cls.paint = Project.create(
            {
                "name": "Opriri la linia de vopsire",
                "loss_type": "downtime",
                "user_id": cls.maria.id,
                "date_start": date(2026, 10, 15),
                "date_deadline": date(2027, 1, 31),
                "baseline_date": date(2026, 10, 14),
                "baseline_value": 7500.0,
                "target_value": 3000.0,
            }
        )
        cls.paint.action_start_analysis()
        env["kaizen.why"].create(
            {"project_id": cls.paint.id, "name": "Pistolul se înfundă la schimbarea culorii", "is_root_cause": True}
        )
        for category, text in (("method", "Spălare fără procedură"), ("machine", "Pistol fără duză de rezervă")):
            env["kaizen.ishikawa.cause"].create({"project_id": cls.paint.id, "category": category, "name": text})
        cls.paint.action_start_actions()
        env["kaizen.action"].create(
            {
                "project_id": cls.paint.id,
                "name": "Procedură de spălare la schimbarea culorii",
                "user_id": cls.maria.id,
                "deadline": date(2026, 11, 5),
            }
        )

        cls.act = env.ref("deltatech_kaizen.kaizen_project_action").id
        cls.menu = env.ref("deltatech_kaizen.menu_kaizen_root").id
        cls.act_actions = env.ref("deltatech_kaizen.kaizen_action_action").id
        cls.act_ishikawa = env.ref("deltatech_kaizen.kaizen_ishikawa_cause_action").id

    # ------------------------------------------------------------------ pașii fluxului

    def _form(self, name, tab=None, highlight=None):
        shot = {
            "url": f"action={self.act}&menu_id={self.menu}&id={self.project.id}&model=kaizen.project&view_type=form",
            "name": name,
            "wait": FORM,
            "settle": 2000,
        }
        if tab:
            shot["click_tab"] = tab
        if highlight:
            shot["highlight"] = highlight
        return shot

    def _to_analysis(self):
        env = self.env
        self.project.action_start_analysis()
        whys = [
            "De ce sunt piese rebutate? Bavura depășește toleranța pe muchia tăiată.",
            "De ce apare bavura? Jocul dintre poanson și placa de tăiere este prea mare.",
            "De ce este jocul prea mare? Muchiile matriței sunt uzate.",
            "De ce sunt muchiile uzate? Matrița nu a fost reascuțită la timp.",
            "De ce nu a fost reascuțită? Nu există un plan de mentenanță preventivă pentru matrițe.",
        ]
        for seq, text in enumerate(whys, start=1):
            env["kaizen.why"].create(
                {"project_id": self.project.id, "sequence": seq, "name": text, "is_root_cause": seq == len(whys)}
            )
        causes = [
            ("man", "Operator nou, neinstruit pe reglaj"),
            ("machine", "Matriță uzată"),
            ("method", "Reglaj fără fișă de lucru"),
            ("material", "Tablă cu grosime variabilă"),
            ("measurement", "Șubler necalibrat"),
            ("environment", "Temperatură variabilă în hală"),
        ]
        for category, text in causes:
            env["kaizen.ishikawa.cause"].create({"project_id": self.project.id, "category": category, "name": text})

    def _to_actions(self):
        env = self.env
        self.project.action_start_actions()
        Action = env["kaizen.action"]
        self.a_plan = Action.create(
            {
                "project_id": self.project.id,
                "name": "Plan de mentenanță preventivă pentru matrițe",
                "user_id": self.andrei.id,
                "deadline": self.today + relativedelta(months=1),
            }
        )
        self.a_sheet = Action.create(
            {
                "project_id": self.project.id,
                "name": "Fișă de reglaj la ștanță",
                "user_id": self.maria.id,
                "deadline": date(2026, 10, 25),
            }
        )
        self.a_sheet.action_done()
        self.a_training = Action.create(
            {
                "project_id": self.project.id,
                "name": "Instruirea operatorilor pe reglaj",
                "user_id": self.maria.id,
                "deadline": date(2026, 11, 10),
            }
        )

    def _to_verification(self):
        (self.a_plan | self.a_training).action_done()
        self.project.action_start_verification()
        self.project.write({"measured_date": self.today, "current_value": 3500.0})

    def _run(self, lang):
        tab_why = {"ro_RO": "5 De ce", "en_US": "5 Why"}
        tab_ishikawa = "Ishikawa"
        tab_actions = {"ro_RO": "Acțiuni", "en_US": "Actions"}
        capture = self.capture_screenshots

        capture(
            [
                self._form(
                    "02_proiect_linie_baza.png",
                    highlight=["label[for^='baseline_value']", "button[name='action_start_analysis']"],
                )
            ],
            lang=lang,
            hide_systray=True,
        )
        self._to_analysis()
        capture(
            [
                self._form("03_analiza_5_de_ce.png", tab=tab_why),
                self._form(
                    "04_analiza_ishikawa.png", tab=tab_ishikawa, highlight="button[name='action_start_actions']"
                ),
            ],
            lang=lang,
            hide_systray=True,
        )
        self._to_actions()
        capture(
            [
                {
                    "url": f"action={self.act}&menu_id={self.menu}&view_type=list",
                    "name": "01_lista_proiecte.png",
                    "wait": LIST,
                },
                self._form("05_actiuni.png", tab=tab_actions),
            ],
            lang=lang,
            hide_systray=True,
        )
        self._to_verification()
        capture(
            [
                self._form(
                    "06_verificare_economii.png",
                    highlight=[
                        "label[for^='current_value']",
                        "label[for^='savings_monthly']",
                        "button[name='action_close']",
                    ],
                ),
                {
                    "url": f"action={self.act_ishikawa}&menu_id={self.menu}&view_type=list",
                    "name": "08_cauze_ishikawa_grupate.png",
                    "wait": LIST,
                    "eval": EXPAND_GROUPS,
                    "settle": 2000,
                },
                {
                    "url": f"action={self.act_actions}&menu_id={self.menu}&view_type=list",
                    "name": "09_lista_actiuni.png",
                    "wait": LIST,
                },
            ],
            lang=lang,
            hide_systray=True,
        )
        self.project.action_close()
        capture(
            [self._form("07_proiect_inchis.png", highlight="label[for^='date_closed']")],
            lang=lang,
            hide_systray=True,
        )

    def test_capture_fise(self):
        self._run("ro_RO")

    def test_capture_usage(self):
        self._run("en_US")
