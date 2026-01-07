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
