from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestMany2oneBadge(HttpCase):
    def test_many2one_badge_hoot(self):
        # Rulăm doar testele legate de widget-ul nostru
        self.browser_js(
            "/web/tests?headless&loglevel=2&preset=desktop&filter=Many2oneBadgeField",
            "",
            "",
            login="admin",
            timeout=1800,
            success_signal="[HOOT] Test suite succeeded",
        )
