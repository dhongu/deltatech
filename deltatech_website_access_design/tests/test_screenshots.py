# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturile fișei consultant (RO) și ale readme/USAGE.md (EN). Seed: vânzătoarea Ana Popescu și
# contabilul Mihai Ionescu, existenți la instalare, rămân în grupul „Access Partners, Sale,
# Invoice”; designerul Ioana Marin e scoasă din grup și primește dreptul standard Website >
# Restricted Editor.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_website_access_design \
#       --test-tags=/deltatech_website_access_design:TestWebsiteAccessDesignScreenshots --stop-after-init
from odoo.tests import tagged

from ..hooks import post_init_hook

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# Deschide tab-ul cu meniurile grupului (Meniuri / Menus).
JS_OPEN_MENUS_TAB = """
() => {
    [...document.querySelectorAll('.o_notebook .nav-link')].find((a) => /^(Meniuri|Menus)$/.test(a.textContent.trim())).click();
}
"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestWebsiteAccessDesignScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_website_access_design"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        group_user = env.ref("base.group_user")

        def user(name, login):
            return env["res.users"].create(
                {"name": name, "login": login, "password": login, "group_ids": [(6, 0, group_user.ids)]}
            )

        user("Ana Popescu", "ana.popescu")
        user("Mihai Ionescu", "mihai.ionescu")
        cls.designer = user("Ioana Marin", "ioana.marin")
        # utilizatorii de mai sus există la instalare: îi adaugă în grup, ca hook-ul real
        post_init_hook(env)
        cls.group = env.ref("deltatech_website_access_design.group_user_internal")
        cls.group.write({"user_ids": [(3, cls.designer.id)]})
        cls.designer.write({"group_ids": [(4, env.ref("website.group_website_restricted_editor").id)]})
        cls.act_groups = env.ref("base.action_res_groups")
        cls.act_users = env.ref("base.action_res_users")

    def _shots(self):
        menu = self.env.ref("base.menu_administration").id
        group_url = f"action={self.act_groups.id}&id={self.group.id}&model=res.groups&view_type=form&menu_id={menu}"
        return [
            {"url": group_url, "name": "01_grup_acces_utilizatori.png", "wait": ".o_form_view", "settle": 2000},
            {
                "url": group_url,
                "name": "02_grup_acces_meniuri.png",
                "wait": ".o_form_view",
                "settle": 2000,
                "eval": JS_OPEN_MENUS_TAB,
                "eval_wait": 1500,
            },
            {
                "url": f"action={self.act_users.id}&id={self.designer.id}&model=res.users&view_type=form",
                "name": "03_utilizator_designer.png",
                "wait": ".o_form_view",
                "settle": 2000,
                "full": True,
            },
        ]

    def _designer_shots(self):
        return [
            {
                "path": "/",
                "name": "04_website_designer.png",
                "wait": "body",
                "settle": 4000,
            },
        ]

    def test_capture_fise(self):
        self.env.flush_all()
        self.capture_screenshots(self._shots(), hide_systray=True)
        self.capture_screenshots(self._designer_shots(), login="ioana.marin", hide_systray=True)

    def test_capture_usage(self):
        self.env.flush_all()
        self.capture_screenshots(self._shots(), hide_systray=True, lang="en_US")
        self.capture_screenshots(self._designer_shots(), login="ioana.marin", hide_systray=True, lang="en_US")
