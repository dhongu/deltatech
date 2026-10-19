# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import HttpCase, tagged

ICON = '<svg viewBox="0 0 64 64"><circle cx="32" cy="32" r="21" fill="#1d5c33"/></svg>'


@tagged("post_install", "-at_install")
class TestCategoryIconGrid(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Category = cls.env["product.public.category"]
        cls.website = cls.env["website"].get_current_website()
        cls.other_website = cls.env["website"].create({"name": "TB Other Website"})
        # Start from a shop without demo categories, so the main categories are known.
        Category.search([]).write({"sequence": 100})
        cls.tractors = Category.create({"name": "TB Grid Tractors", "sequence": 1, "icon_svg": ICON})
        cls.seeds = Category.create({"name": "TB Grid Seeds", "sequence": 2})
        cls.parts = Category.create({"name": "TB Grid Parts", "sequence": 3, "parent_id": cls.tractors.id})
        cls.foreign = Category.create({"name": "TB Grid Foreign", "sequence": 4, "website_id": cls.other_website.id})
        cls.empty = Category.create({"name": "TB Grid Empty", "sequence": 5})
        cls.env["product.template"].create(
            {
                "name": "TB Grid Product",
                "is_published": True,
                "sale_ok": True,
                "public_categ_ids": [(6, 0, (cls.tractors | cls.seeds | cls.parts | cls.foreign).ids)],
            }
        )

    def _grid(self, **params):
        self.authenticate(None, None)
        return self.make_jsonrpc_request("/website/snippet/category_icon_grid", params)

    def test_main_categories(self):
        Category = self.env["product.public.category"]
        categories = Category._get_icon_grid_categories(self.website, limit=3)
        self.assertEqual(categories[:2], self.tractors | self.seeds)
        self.assertNotIn(self.parts, categories)
        self.assertNotIn(self.foreign, Category._get_icon_grid_categories(self.website, limit=48))
        self.assertIn(self.foreign, Category._get_icon_grid_categories(self.other_website, limit=48))

    def test_chosen_categories_keep_their_order(self):
        Category = self.env["product.public.category"]
        chosen = [self.parts.id, self.seeds.id, self.foreign.id, self.tractors.id]
        categories = Category._get_icon_grid_categories(self.website, chosen)
        # The category of the other website is left out.
        self.assertEqual(categories.ids, [self.parts.id, self.seeds.id, self.tractors.id])
        self.assertEqual(Category._get_icon_grid_categories(self.website, chosen, limit=2).ids, chosen[:2])

    def test_limit_is_bounded(self):
        Category = self.env["product.public.category"]
        self.assertEqual(len(Category._get_icon_grid_categories(self.website, limit=1)), 1)
        self.assertLessEqual(len(Category._get_icon_grid_categories(self.website, limit=0)), 12)
        self.assertLessEqual(len(Category._get_icon_grid_categories(self.website, limit=1000)), 48)

    def test_rendered_grid(self):
        html = self._grid(category_ids=[self.tractors.id, self.seeds.id])
        slug = self.env["ir.http"]._slug
        self.assertIn(f'href="/shop/category/{slug(self.tractors)}"', html)
        self.assertIn(f'href="/shop/category/{slug(self.seeds)}"', html)
        self.assertIn('<circle cx="32" cy="32" r="21" fill="#1d5c33"/>', html)
        # One icon for two categories: the category without an icon shows only its name.
        self.assertEqual(html.count('class="s_category_icon_grid_icon o_category_icon"'), 1)
        self.assertIn("TB Grid Seeds", html)
        self.assertLess(html.index("TB Grid Tractors"), html.index("TB Grid Seeds"))

    def test_visitors_see_only_categories_with_products(self):
        html = self._grid(category_ids=[self.empty.id, self.seeds.id])
        self.assertNotIn("TB Grid Empty", html)
        self.assertIn("TB Grid Seeds", html)
        self.assertEqual(self._grid(category_ids=[self.empty.id]), "")

    def test_snippet_from_editor(self):
        self.start_tour("/", "deltatech_website_category_icon.category_icon_grid", login="admin")
        page = self.env["website"].with_context(website_id=self.website.id).viewref("website.homepage")
        arch = page.arch_db
        self.assertIn('data-snippet="s_category_icon_grid"', arch)
        self.assertIn("s_category_icon_grid_icon_lg", arch)
        self.assertIn('data-mode="manual"', arch)
        self.assertIn(f"&quot;id&quot;:{self.seeds.id}", arch.replace(" ", ""))
        # Only the options are saved: the items come from the database on each visit.
        self.assertNotIn("TB Grid Tractors", arch)
