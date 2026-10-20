# ©  2008-2026 Terrabit
# See README.rst file on addons root folder for license details

from lxml import html as lxml_html

from odoo.tests import HttpCase, new_test_user, tagged

# Counts the autocomplete requests: a 3-letter term sends none, a 4-letter one sends one, after
# the 800 ms debounce (none yet 500 ms after typing).
SEARCHBAR_JS = """
(async () => {
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    let input;
    for (let i = 0; i < 100; i++) {
        input = document.querySelector(".o_header_searchbar .search-query");
        if (input && input.getAttribute("autocomplete") === "off") {
            break;
        }
        await sleep(100);
    }
    if (!input || input.getAttribute("autocomplete") !== "off") {
        console.error("the search bar interaction did not start");
        return;
    }
    let calls = 0;
    const open = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function (method, url, ...args) {
        if (String(url).includes("/website/snippet/autocomplete")) {
            calls++;
        }
        return open.call(this, method, url, ...args);
    };
    const type = (value) => {
        input.value = value;
        input.dispatchEvent(new Event("input", {bubbles: true}));
    };
    type("abc");
    await sleep(1200);
    if (calls) {
        console.error("autocomplete requested for a 3-letter term");
        return;
    }
    type("abcd");
    await sleep(500);
    if (calls) {
        console.error("autocomplete requested before the 800 ms debounce");
        return;
    }
    await sleep(1000);
    if (calls !== 1) {
        console.error(`expected one autocomplete request, got ${calls}`);
        return;
    }
    console.log("test successful");
})();
"""


@tagged("post_install", "-at_install")
class TestWebsiteSearchbar(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env.ref("base.default_website")
        cls.website.header_search_limit = 6
        cls.portal_user = new_test_user(
            cls.env, login="dt_searchbar_portal", groups="base.group_portal", name="Portal Search"
        )

    def _assert_header_searchbar(self):
        response = self.url_open("/")
        self.assertEqual(response.status_code, 200)
        tree = lxml_html.fromstring(response.content)
        self.assertTrue(
            tree.xpath("//form[contains(@class, 'o_header_searchbar')]//input[contains(@class, 'search-query')]")
        )

    def test_homepage_public_visitor(self):
        self._assert_header_searchbar()

    def test_homepage_portal_user(self):
        self.authenticate(self.portal_user.login, self.portal_user.login)
        self._assert_header_searchbar()

    def test_asset_in_frontend_bundle(self):
        bundle = self.env["ir.qweb"]._get_asset_bundle("web.assets_frontend", debug_assets=True)
        self.assertIn(
            "/deltatech_website_searchbar/static/src/js/searchbar.esm.js",
            [file["url"] for file in bundle.files],
        )

    def test_autocomplete_min_length_and_debounce(self):
        self.browser_js("/", SEARCHBAR_JS, login=None)
