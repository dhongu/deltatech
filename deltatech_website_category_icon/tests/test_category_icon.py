# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.exceptions import ValidationError
from odoo.tests import HttpCase, TransactionCase, tagged

TRACTOR = (
    '<svg viewBox="0 0 64 64" width="64" height="64">'
    '<rect width="64" height="64" rx="14" fill="#e7f0e4"/>'
    '<g transform="translate(2, 0)">'
    '<path d="M9 35a4 4 0 0 1 4-4h20v13H9z" fill="#1d5c33"/>'
    '<circle cx="42" cy="44" r="11.5" fill="rgb(20, 58, 32)"/>'
    "</g></svg>"
)


@tagged("post_install", "-at_install")
class TestCategoryIconSanitize(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.env["product.public.category"].create({"name": "TB Tractoare"})

    def test_clean_icon_is_kept(self):
        self.category.icon_svg = TRACTOR
        icon = self.category.icon_svg
        self.assertTrue(icon.startswith('<svg xmlns="http://www.w3.org/2000/svg"'))
        self.assertIn('viewBox="0 0 64 64"', icon)
        self.assertIn('aria-hidden="true"', icon)
        self.assertNotIn("width=", icon.split(">", 1)[0])
        self.assertIn('d="M9 35a4 4 0 0 1 4-4h20v13H9z"', icon)
        self.assertIn("translate(2, 0)", icon)
        self.assertIn(icon, str(self.category.icon_preview))

    def test_namespaced_icon_is_accepted(self):
        self.category.icon_svg = TRACTOR.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ')
        self.assertIn("<circle", self.category.icon_svg)
        self.assertNotIn('xmlns=""', self.category.icon_svg)

    def test_current_color_is_kept(self):
        # Outline icons drawn with currentColor take the color of the link text.
        self.category.icon_svg = '<svg viewBox="0 0 64 64"><path d="M8 8h48" stroke="currentColor" fill="none"/></svg>'
        self.assertIn('stroke="currentColor"', self.category.icon_svg)

    def test_inherited_icon(self):
        Category = self.env["product.public.category"]
        self.category.icon_svg = TRACTOR
        child = Category.create({"name": "TB Child", "parent_id": self.category.id})
        grandchild = Category.create({"name": "TB Grandchild", "parent_id": child.id})
        self.assertEqual(str(grandchild.icon_inherited_html), self.category.icon_svg)
        self.assertFalse(self.category.icon_inherited_html)
        # The closest parent with an icon wins.
        child.icon_svg = '<svg viewBox="0 0 64 64"><circle cx="32" cy="32" r="9"/></svg>'
        self.assertEqual(str(grandchild.icon_inherited_html), child.icon_svg)

    def test_create_sanitizes(self):
        category = self.env["product.public.category"].create({"name": "TB Combine", "icon_svg": TRACTOR})
        self.assertIn('aria-hidden="true"', category.icon_svg)

    def test_clear_icon(self):
        self.category.icon_svg = TRACTOR
        self.category.icon_svg = False
        self.assertFalse(self.category.icon_svg)
        self.assertFalse(self.category.icon_html)

    def test_forbidden_content_is_rejected(self):
        bad_icons = {
            "script": '<svg viewBox="0 0 64 64"><script>alert(1)</script></svg>',
            "event handler": '<svg viewBox="0 0 64 64" onload="alert(1)"><rect width="1" height="1"/></svg>',
            "external image": '<svg viewBox="0 0 64 64"><image href="https://x.test/a.png"/></svg>',
            "use reference": '<svg viewBox="0 0 64 64"><use href="#a"/></svg>',
            "style element": '<svg viewBox="0 0 64 64"><style>*{fill:red}</style></svg>',
            "style attribute": '<svg viewBox="0 0 64 64"><rect style="fill:red" width="1" height="1"/></svg>',
            "url fill": '<svg viewBox="0 0 64 64"><rect fill="url(https://x.test/#a)" width="1" height="1"/></svg>',
            "foreign object": '<svg viewBox="0 0 64 64"><foreignObject><div/></foreignObject></svg>',
            "html element": '<svg viewBox="0 0 64 64"><a xmlns="http://www.w3.org/1999/xhtml"/></svg>',
            "no viewBox": '<svg width="64" height="64"><rect width="1" height="1"/></svg>',
            "not svg": "<div>hello</div>",
            "not xml": "<svg viewBox='0 0 64 64'><rect></svg>",
            "entity": '<!DOCTYPE svg [<!ENTITY x SYSTEM "file:///etc/passwd">]><svg viewBox="0 0 64 64"><title>&x;</title></svg>',
            "too large": '<svg viewBox="0 0 64 64">' + '<rect width="1" height="1"/>' * 1000 + "</svg>",
        }
        for case, svg in bad_icons.items():
            with self.subTest(case=case), self.assertRaises(ValidationError):
                self.category.icon_svg = svg


@tagged("post_install", "-at_install")
class TestCategoryIconShop(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.ref("website_sale.products_categories").active = True
        Category = cls.env["product.public.category"]
        cls.category = Category.create({"name": "TB Icon Category", "icon_svg": TRACTOR})
        cls.child = Category.create({"name": "TB Icon Child", "parent_id": cls.category.id})
        cls.env["product.template"].create(
            {
                "name": "TB Icon Product",
                "is_published": True,
                "sale_ok": True,
                "public_categ_ids": [(6, 0, (cls.category | cls.child).ids)],
            }
        )
        cls.website = cls.env["website"].get_current_website()

    def test_icon_in_category_list(self):
        response = self.url_open("/shop")
        self.assertEqual(response.status_code, 200)
        self.assertIn('class="o_category_icon o_category_icon_sm"', response.text)
        # Icon and name share an inner flex span, so the layout does not depend on
        # how the theme styles the link.
        self.assertRegex(
            response.text,
            r'<span class="o_category_link d-inline-flex align-items-center gap-2">\s*'
            r'<span class="o_category_icon o_category_icon_sm">',
        )
        self.assertIn('d="M9 35a4 4 0 0 1 4-4h20v13H9z"', response.text)
        self.assertIn("TB Icon Category", response.text)

    def test_inherited_icon_in_category_list(self):
        icon = 'class="o_category_icon o_category_icon_sm"'
        # The shop renders the category list more than once (sidebar and mobile
        # off-canvas), so compare counts rather than expect a fixed number.
        self.website.category_icon_inherit = False
        own = self.url_open("/shop").text.count(icon)
        self.assertGreater(own, 0)
        # With the option, the child without its own icon shows the parent's.
        self.website.category_icon_inherit = True
        self.assertEqual(self.url_open("/shop").text.count(icon), 2 * own)
