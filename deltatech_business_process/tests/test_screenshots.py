# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Procese de implementare" — generate în timpul testelor,
# în limba RO, pe compania implementatorului „Demo Consultanță SRL".
#
# Seed: proiectul „Odoo Mobila Nord" pentru clientul Mobila Nord SRL, cu
# cinci procese în stări diferite, ca ecranele să arate tot ciclul de viață:
#   - VZ01 Ofertare și comandă client (Vânzări) — testele intern, de integrare și de
#     acceptanță finalizate, proces trecut în producție;
#   - VZ02 Retururi de la clienți (Vânzări) — în test: acceptanța rulează, pasul
#     „Emitere notă de credit" a picat și are un issue deschis;
#   - AC01 Aprovizionare de la furnizori (Achiziții) — în design;
#   - ST01 Inventar anual (Stocuri) — ciornă;
#   - CT01 Transmitere e-Factura (Contabilitate) — gata de producție.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_business_process,l10n_ro_doc_screenshots,l10n_ro_process_library \
#       --test-tags=/deltatech_business_process:TestBusinessProcessScreenshots --stop-after-init
# l10n_ro_process_library e opțional: fără el se sare doar captura bibliotecii de procese.
import unittest
from datetime import timedelta

from odoo import Command, fields
from odoo.tests import tagged

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# Deschide meniul „Acțiuni" (⚙) al ecranului curent și alege intrarea potrivită; pe listă
# selectează întâi toate rândurile, pentru că acțiunile se leagă de înregistrările bifate.
JS_ACTION_MENU = """
async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const row = %(row)s;
    const selector = row
        ? [...document.querySelectorAll('.o_data_row')].find((r) => row.test(r.textContent))
            ?.querySelector('.o_list_record_selector input')
        : document.querySelector('thead .o_list_record_selector input');
    if (selector) {
        selector.click();
        await sleep(1000);
    }
    const toggle = [...document.querySelectorAll('.o_control_panel button')].find((b) =>
        /Acțiuni|Actions/.test(b.textContent + (b.title || '') + (b.getAttribute('aria-label') || ''))
    );
    toggle.click();
    await sleep(1000);
    const match = %(match)s;
    if (match) {
        const items = [...document.querySelectorAll('.o-dropdown-item, .dropdown-item')];
        items.find((e) => match.test(e.textContent)).click();
        await sleep(2500);
    }
    const next = %(next)s;
    if (next) {
        [...document.querySelectorAll('.modal-footer button')].find((b) => next.test(b.textContent)).click();
        await sleep(3000);
        // biblioteca se deschide grupată pe arie: desfacem primul grup, ca să se vadă procesele
        const group = document.querySelector('.modal .o_group_header');
        if (group) {
            group.click();
            await sleep(2000);
        }
        document.activeElement?.blur();
    }
}
"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestBusinessProcessScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_business_process"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Consultanță SRL")
        env = cls.env
        company = cls.company = env.company
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        (admin | env.user).tz = "Europe/Bucharest"
        manager = env.ref("deltatech_business_process.group_business_process_manager")
        (admin | env.user).group_ids = [Command.link(manager.id)]
        env.flush_all()

        today = fields.Date.today()
        Partner = env["res.partner"]
        customer = Partner.create({"name": "Mobila Nord SRL", "is_company": True, "city": "Suceava"})
        cls.support = Partner.create({"name": "Radu Ene", "email": "radu.ene@example.ro"})
        cls.key_user = Partner.create(
            {"name": "Ioana Rusu", "parent_id": customer.id, "email": "ioana.rusu@example.ro"}
        )
        cls.warehouse_user = Partner.create(
            {"name": "Mihai Stan", "parent_id": customer.id, "email": "mihai.stan@example.ro"}
        )

        # consultantul și managerul de proiect sunt utilizatori: VZ02 e vizibil doar lor
        def user(name, login):
            return (
                env["res.users"]
                .with_context(no_reset_password=True)
                .create(
                    {
                        "name": name,
                        "login": login,
                        "email": f"{login}@example.ro",
                        "company_id": company.id,
                        "company_ids": [Command.set(company.ids)],
                        "group_ids": [
                            Command.set(env.ref("deltatech_business_process.group_business_process_responsible").ids)
                        ],
                    }
                )
            )

        cls.consultant_user = user("Andrei Popa", "andrei.popa")
        cls.pm_user = user("Elena Marin", "elena.marin")
        cls.consultant = cls.consultant_user.partner_id
        pm = cls.pm_user.partner_id

        cls.project = env["business.project"].create(
            {
                "name": "Odoo Mobila Nord",
                "customer_id": customer.id,
                "project_manager_id": pm.id,
                "responsible_id": cls.consultant.id,
                "state": "realization",
                "date_start": today - timedelta(days=60),
                "date_go_live": today + timedelta(days=30),
            }
        )

        Area = env["business.area"]
        area_sale = Area.create({"name": "Vânzări", "responsible_id": cls.consultant.id})
        area_purchase = Area.create({"name": "Achiziții", "responsible_id": cls.consultant.id})
        area_stock = Area.create({"name": "Stocuri", "responsible_id": cls.support.id})
        area_account = Area.create({"name": "Contabilitate", "responsible_id": cls.support.id})
        group_order = env["business.process.group"].create({"name": "Comandă — încasare", "area_id": area_sale.id})
        stage = env["business.process.implementation.stage"].search([], limit=1)

        def process(code, name, area, steps, durations, **extra):
            vals = {
                "code": code,
                "name": name,
                "area_id": area.id,
                "project_id": cls.project.id,
                "customer_id": cls.key_user.id,
                "support_id": cls.support.id,
                "implementation_stage_id": stage.id,
                "module_type": "standard",
                "configuration_duration": durations[0],
                "instructing_duration": durations[1],
                "data_migration_duration": durations[2],
                "testing_duration": durations[3],
                "step_ids": [
                    Command.create({"sequence": (i + 1) * 10, "name": step, "responsible_id": resp.id})
                    for i, (step, resp) in enumerate(steps)
                ],
            }
            vals.update(extra)
            return env["business.process"].create(vals)

        ku, wu = cls.key_user, cls.warehouse_user
        cls.p_order = process(
            "VZ01",
            "Ofertare și comandă client",
            area_sale,
            [("Creare ofertă", ku), ("Confirmare comandă", ku), ("Livrare marfă", wu), ("Emitere factură", ku)],
            (6.0, 3.0, 2.0, 4.0),
            process_group_id=group_order.id,
            description="<p>Fluxul complet de la cererea de ofertă a clientului până la factură.</p>",
        )
        cls.p_return = process(
            "VZ02",
            "Retururi de la clienți",
            area_sale,
            [
                ("Înregistrare cerere de retur", ku),
                ("Recepție marfă returnată", wu),
                ("Emitere notă de credit", ku),
            ],
            (3.0, 1.5, 0.0, 2.0),
            process_group_id=group_order.id,
            allowed_user_ids=[Command.set((cls.consultant_user | cls.pm_user).ids)],
        )
        cls.p_purchase = process(
            "AC01",
            "Aprovizionare de la furnizori",
            area_purchase,
            [("Cerere de ofertă furnizor", ku), ("Comandă de achiziție", ku), ("Recepție", wu)],
            (4.0, 2.0, 1.0, 2.5),
        )
        cls.p_inventory = process(
            "ST01",
            "Inventar anual",
            area_stock,
            [("Listă de inventar", wu), ("Numărare", wu), ("Validare diferențe", wu)],
            (2.0, 1.0, 0.0, 1.0),
        )
        cls.p_einvoice = process(
            "CT01",
            "Transmitere e-Factura",
            area_account,
            [("Configurare SPV", ku), ("Trimitere factură", ku), ("Preluare mesaje ANAF", ku)],
            (3.0, 1.0, 0.0, 1.5),
        )
        processes = cls.p_order | cls.p_return | cls.p_purchase | cls.p_einvoice
        processes.button_start_design()
        (cls.p_order | cls.p_return | cls.p_einvoice).button_start_test()

        # VZ01: toate cele trei teste finalizate, apoi trecerea în producție
        for scope in ("internal", "integration", "user_acceptance"):
            test = cls.p_order._start_test(scope)
            test.tester_id = cls.key_user if scope == "user_acceptance" else cls.consultant
            test.action_run()
            test.test_step_ids.write({"result": "passed", "date_end": today - timedelta(days=5)})
            test.action_done()
        cls.p_order.button_go_live()
        # CT01: testele închise, procesul gata de producție
        cls.p_einvoice.button_end_test()

        # VZ02: acceptanța clientului rulează — primul pas trecut, al treilea a picat
        cls.test_return = cls.p_return._start_test("user_acceptance")
        cls.test_return.tester_id = cls.key_user
        cls.test_return.action_run()
        steps = cls.test_return.test_step_ids.sorted("sequence")
        steps[0].write(
            {
                "result": "passed",
                "data_used": "Cerere retur RET/0012, 2 buc. Scaun Nordic",
                "data_result": "Cerere înregistrată",
                "date_end": today,
            }
        )
        steps[1].write({"data_used": "Recepție pe Depozit central"})
        cls.failed_step = steps[2]
        cls.failed_step.write({"data_used": "Factura FV 0158, 2 buc. Scaun Nordic"})
        cls.issue = env["business.issue"].create(
            {
                "name": "Nota de credit nu preia prețul din factura inițială",
                "project_id": cls.project.id,
                "process_id": cls.p_return.id,
                "area_id": area_sale.id,
                "step_test_id": cls.failed_step.id,
                "raise_by_id": cls.key_user.id,
                "responsible_id": cls.consultant.id,
                "customer_id": cls.key_user.id,
                "severity": "major",
                "category": "defect",
                "description": "La returul a 2 buc. Scaun Nordic, nota de credit se propune cu prețul de "
                "listă curent, nu cu prețul din factura FV 0158.",
            }
        )
        cls.issue.button_send()
        # alte două probleme, ca rapoartele să arate mai multe severități și stări
        spv_issue = env["business.issue"].create(
            {
                "name": "Mesajele SPV nu se descarcă automat",
                "project_id": cls.project.id,
                "process_id": cls.p_einvoice.id,
                "area_id": area_account.id,
                "responsible_id": cls.support.id,
                "severity": "critical",
                "category": "defect",
            }
        )
        spv_issue.button_send()
        spv_issue.button_in_progress()
        spv_issue.write(
            {"solution": "Programată acțiunea de preluare a mesajelor la 30 de minute.", "solution_date": today}
        )
        spv_issue.button_solved()
        offer_issue = env["business.issue"].create(
            {
                "name": "Termenul de livrare lipsește din ofertă",
                "project_id": cls.project.id,
                "process_id": cls.p_order.id,
                "area_id": area_sale.id,
                "responsible_id": cls.consultant.id,
                "severity": "minor",
                "category": "improvement",
            }
        )
        offer_issue.button_send()
        offer_issue.button_in_progress()
        offer_issue.write({"solution": "Câmpul Termen livrare adăugat în ofertă.", "solution_date": today})
        offer_issue.button_solved()
        offer_issue.button_in_test()
        offer_issue.write({"closed_date": today})
        offer_issue.button_done()

        # o dezvoltare cerută de proces, legată de pasul care a picat
        dev_type = env["business.development.type"].create({"name": "Raport"})
        cls.development = env["business.development"].create(
            {
                "name": "Raport retururi pe motiv",
                "area_id": area_sale.id,
                "type_id": dev_type.id,
                "project_id": cls.project.id,
                "responsible_id": cls.consultant.id,
                "customer_id": cls.key_user.id,
                "development_duration": 8.0,
                "state": "specification",
            }
        )
        cls.failed_step.step_id.development_ids = [Command.link(cls.development.id)]
        cls.project.calculate_total_project_duration()

        cls.act_project = env.ref("deltatech_business_process.action_business_project")
        cls.act_process = env.ref("deltatech_business_process.action_business_process")
        cls.act_test = env.ref("deltatech_business_process.action_business_process_test")
        cls.act_issue = env.ref("deltatech_business_process.action_business_issue")
        cls.act_report = env.ref("deltatech_business_process.action_business_process_report")
        cls.act_test_report = env.ref("deltatech_business_process.action_business_process_test_report")
        cls.act_issue_report = env.ref("deltatech_business_process.action_business_issue_report")
        cls.act_settings = env.ref("deltatech_business_process.action_business_process_config_settings")
        cls.has_library = bool(
            env["ir.module.module"].search([("name", "=", "l10n_ro_process_library"), ("state", "=", "installed")])
        )

    def _capture(self, shots):
        self.env.flush_all()
        self.capture_screenshots(shots)
        self.env.invalidate_all()

    def _form(self, action, record, name, **extra):
        shot = {
            "url": f"action={action.id}&id={record.id}&model={record._name}&view_type=form",
            "name": name,
            "wait": ".o_form_view",
            "settle": 2500,
        }
        shot.update(extra)
        return shot

    def test_capture_fise(self):
        shots = [
            {
                "url": f"action={self.act_project.id}&view_type=kanban",
                "name": "01_proiecte.png",
                "wait": ".o_kanban_view",
                "settle": 2000,
            },
            self._form(
                self.act_project,
                self.project,
                "02_proiect.png",
                highlight=["button[name='calculate_total_project_duration']"],
            ),
            {
                "url": f"action={self.act_process.id}&view_type=list",
                "name": "03_procese.png",
                "wait": ".o_list_view",
                "settle": 2000,
            },
            self._form(
                self.act_process,
                self.p_return,
                "04_proces_pasi.png",
                highlight=[".o_notebook_headers a[name='steps']"],
            ),
            self._form(
                self.act_process,
                self.p_return,
                "05_proces_durate.png",
                click_tab="Durată",
            ),
            self._form(
                self.act_process,
                self.p_return,
                "06_proces_responsabili.png",
                click_tab="Responsabil",
            ),
            {
                "url": f"action={self.act_process.id}&view_type=list",
                "name": "07_pornire_teste.png",
                "wait": ".o_list_view",
                "settle": 2000,
                "eval": JS_ACTION_MENU % {"row": "/VZ02/", "match": "null", "next": "null"},
                "eval_wait": 1500,
            },
            self._form(
                self.act_test,
                self.test_return,
                "08_test_acceptanta.png",
                highlight=["button[name='action_view_issue']"],
            ),
            self._form(
                self.act_issue,
                self.issue,
                "09_issue.png",
                highlight=["button[name='button_in_progress']"],
            ),
            {
                "url": f"action={self.act_report.id}&view_type=pivot",
                "name": "10_raport_procese.png",
                "wait": ".o_pivot",
                "settle": 2500,
            },
            {
                "url": f"action={self.act_test_report.id}&view_type=pivot",
                "name": "11_raport_teste.png",
                "wait": ".o_pivot",
                "settle": 2500,
            },
            {
                "url": f"action={self.act_issue_report.id}&view_type=pivot",
                "name": "12_raport_issues.png",
                "wait": ".o_pivot",
                "settle": 2500,
            },
            self.xlsx_shot(
                self.project.with_context(lang="ro_RO").generate_excel_report(),
                "13_raport_excel_proiect.png",
                title="Project_Report.xlsx",
            ),
            {
                "url": f"action={self.act_process.id}&view_type=list",
                "name": "14_export_json.png",
                "wait": ".o_list_view",
                "settle": 2000,
                "eval": JS_ACTION_MENU % {"row": "null", "match": "/Export.*(proces|Process)/i", "next": "null"},
                "eval_wait": 1500,
            },
            {
                "url": f"action={self.act_settings.id}",
                "name": "16_setari_biblioteca.png",
                "wait": ".o_form_view",
                "timeout": 40000,
                "settle": 3000,
                "eval": "document.querySelector(\"div[name='process_library_sources']\")"
                ".scrollIntoView({block: 'start'})",
            },
        ]
        if self.has_library:
            shots.insert(
                -1,
                self._form(
                    self.act_project,
                    self.project,
                    "15_biblioteca_procese.png",
                    eval=JS_ACTION_MENU % {"row": "null", "match": "/bibliotec|library/i", "next": "/Continu/"},
                    eval_wait=2000,
                ),
            )
        self._capture(shots)
