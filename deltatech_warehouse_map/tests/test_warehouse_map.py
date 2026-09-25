from odoo.tests.common import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestWarehouseMap(HttpCase):
    def test_01_map_home(self):
        self.authenticate("admin", "admin")
        response = self.url_open("/deltatech/warehouse_map")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Hartă Depozit", response.text)

    def test_02_location_map(self):
        self.authenticate("admin", "admin")
        location = self.env.ref("stock.stock_location_stock")
        response = self.url_open(f"/deltatech/warehouse_map/location/{location.id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(location.name, response.text)


@tagged("post_install", "-at_install")
class TestWarehouseMapAccess(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.ref("base.main_company")
        cls.company_b = cls.env["res.company"].create({"name": "Warehouse Map Company B"})
        cls.location_a = (
            cls.env["stock.warehouse"].search([("company_id", "=", cls.company_a.id)], limit=1).lot_stock_id
        )
        cls.location_b = (
            cls.env["stock.warehouse"].search([("company_id", "=", cls.company_b.id)], limit=1).lot_stock_id
        )
        cls.shelf_a = cls.env["stock.location"].create(
            {"name": "WMAP Shelf A", "location_id": cls.location_a.id, "usage": "internal"}
        )
        stock_group = cls.env.ref("stock.group_stock_user")
        cls.env["res.users"].create(
            {
                "name": "WMAP Portal",
                "login": "wmap_portal",
                "password": "wmap_portal",
                "group_ids": [(6, 0, [cls.env.ref("base.group_portal").id])],
            }
        )
        cls.env["res.users"].create(
            {
                "name": "WMAP Internal",
                "login": "wmap_internal",
                "password": "wmap_internal",
                "group_ids": [(6, 0, [cls.env.ref("base.group_user").id])],
            }
        )
        cls.env["res.users"].create(
            {
                "name": "WMAP Stock A",
                "login": "wmap_stock_a",
                "password": "wmap_stock_a",
                "company_id": cls.company_a.id,
                "company_ids": [(6, 0, cls.company_a.ids)],
                "group_ids": [(6, 0, [stock_group.id])],
            }
        )
        cls.env["res.users"].create(
            {
                "name": "WMAP Stock B",
                "login": "wmap_stock_b",
                "password": "wmap_stock_b",
                "company_id": cls.company_b.id,
                "company_ids": [(6, 0, cls.company_b.ids)],
                "group_ids": [(6, 0, [stock_group.id])],
            }
        )

    def _get(self, login, location):
        self.authenticate(login, login)
        return self.url_open(f"/deltatech/warehouse_map/location/{location.id}")

    def test_portal_user_not_found(self):
        self.assertEqual(self._get("wmap_portal", self.location_a).status_code, 404)
        self.assertEqual(self.url_open("/deltatech/warehouse_map").status_code, 404)

    def test_internal_user_without_stock_not_found(self):
        self.assertEqual(self._get("wmap_internal", self.location_a).status_code, 404)

    def test_stock_user_ok(self):
        response = self._get("wmap_stock_a", self.location_a)
        self.assertEqual(response.status_code, 200)
        self.assertIn("WMAP Shelf A", response.text)

    def test_stock_user_other_company(self):
        self.assertEqual(self._get("wmap_stock_b", self.location_a).status_code, 404)
        self.assertEqual(self._get("wmap_stock_b", self.shelf_a).status_code, 404)
        response = self._get("wmap_stock_b", self.location_b)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("WMAP Shelf A", response.text)
