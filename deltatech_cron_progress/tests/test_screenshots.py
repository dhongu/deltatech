# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Acțiuni programate care lucrează pe loturi până termină",
# în limba RO.
#
# Seedează două acțiuni planificate de test, de tip cod:
# - „Demo: procesare pe loturi" procesează 25 de înregistrări pe loturi de 10; contorul celor
#   procesate stă în parametrul de sistem ``deltatech_cron_progress.demo_done``;
# - „Demo: lot fără progres" raportează înregistrări rămase fără să proceseze vreuna.
# Ambele sunt pornite cu „Rulează manual" în timpul capturilor.
#
# Rulare:
#   .venv/bin/python odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_cron_progress,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    try:
        from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
    except ImportError:
        ScreenshotCase = None

DEMO_PARAM = "deltatech_cron_progress.demo_done"

BATCH_CODE = f"""# 25 de înregistrări, procesate pe loturi de câte 10
total = 25
done_before = env['ir.config_parameter'].get_int('{DEMO_PARAM}')
batch = min(10, total - done_before)
env['ir.config_parameter'].set_int('{DEMO_PARAM}', done_before + batch)
env['ir.cron']._cron_report_progress(batch, total - done_before - batch)
"""

STUCK_CODE = """# 5 înregistrări rămase, dar niciuna nu poate fi procesată
env['ir.cron']._cron_report_progress(0, 5)
"""

RUN_MANUALLY = "button[name='method_direct_trigger']"


@tagged("-at_install", "post_install", "fise_screenshots")
class TestCronProgressScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_cron_progress"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots / l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.activate_ro_lang()
        cls.force_light_theme()
        model = cls.env.ref("base.model_ir_config_parameter")
        cls.env["ir.config_parameter"].set_int(DEMO_PARAM, 0)
        cls.cron_batch = cls.env["ir.cron"].create(
            {
                "name": "Demo: procesare pe loturi",
                "model_id": model.id,
                "state": "code",
                "code": BATCH_CODE,
                "interval_number": 1,
                "interval_type": "days",
            }
        )
        cls.cron_stuck = cls.env["ir.cron"].create(
            {
                "name": "Demo: lot fără progres",
                "model_id": model.id,
                "state": "code",
                "code": STUCK_CODE,
                "interval_number": 1,
                "interval_type": "days",
            }
        )
        cls.param_action = cls.env.ref("base.ir_config_list_action").id

    def _cron_url(self, cron):
        return f"id={cron.id}&model=ir.cron&view_type=form"

    def _shots(self):
        return [
            {
                "url": self._cron_url(self.cron_batch),
                "name": "01_actiune_planificata.png",
                "wait": ".o_form_view",
                "highlight": [RUN_MANUALLY, "div[name='code']"],
                "full": True,
            },
            {
                "url": self._cron_url(self.cron_batch),
                "name": "02_dupa_rulare_manuala.png",
                "wait": ".o_form_view",
                "click_btn": RUN_MANUALLY,
                "wait_after": ".o_form_view",
                "settle": 3000,
                "highlight": ["div[name='nextcall']"],
                "full": True,
            },
            {
                "url": f"action={self.param_action}&view_type=list",
                "name": "03_inregistrari_procesate.png",
                "wait": ".o_list_view",
                "highlight": [f"tr.o_data_row:has-text('{DEMO_PARAM}')"],
            },
            {
                "url": self._cron_url(self.cron_stuck),
                "name": "04_lot_fara_progres.png",
                "wait": ".o_form_view",
                "click_btn": RUN_MANUALLY,
                "wait_after": ".o_form_view",
                "settle": 3000,
                "highlight": ["div[name='code']", "div[name='nextcall']"],
                "full": True,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots())
