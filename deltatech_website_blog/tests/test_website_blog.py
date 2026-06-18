from datetime import datetime

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestWebsiteBlogOrder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.blog = cls.env["blog.blog"].create({"name": "Ordering test blog"})

    def _create_post(self, name, published_date):
        return self.env["blog.post"].create(
            {
                "name": name,
                "blog_id": self.blog.id,
                "published_date": published_date,
            }
        )

    def test_default_order_uses_publication_date_and_id(self):
        older = self._create_post("Older", datetime(2026, 1, 1))
        newer_first = self._create_post("Newer first", datetime(2026, 2, 1))
        newer_last = self._create_post("Newer last", datetime(2026, 2, 1))

        posts = self.env["blog.post"].search([("blog_id", "=", self.blog.id)])

        self.assertEqual(posts, newer_last | newer_first | older)
