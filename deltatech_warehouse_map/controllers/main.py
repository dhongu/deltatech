from odoo import http
from odoo.http import request


class WarehouseMapController(http.Controller):
    @http.route("/deltatech/warehouse_map", type="http", auth="user")
    def map_home(self, **kwargs):
        # Pagină de pornire minimă: listăm rădăcina Stock și oferim link către hartă generică
        stock = request.env.ref("stock.stock_location_stock", raise_if_not_found=False)
        return request.render(
            "deltatech_warehouse_map.view_location_generic",
            {
                "location": stock,
                "children": stock and stock.child_ids.sorted(key=lambda l: l.name) or [],
            },
        )

    @http.route("/deltatech/warehouse_map/location/<int:loc_id>", type="http", auth="user")
    def view_location(self, loc_id, **kwargs):
        # Afișare generică: pentru o locație selectată, afișează copiii pe linii,
        # iar pentru fiecare copil afișează copiii lui pe o a doua linie (defalcare).
        location = request.env["stock.location"].sudo().browse(loc_id).exists()
        if not location:
            return request.not_found()

        children = request.env["stock.location"].sudo().search([("location_id", "=", location.id)], order="name")

        # Preluăm pentru fiecare copil lista de nepoți (următorul nivel)
        # folosim IDs ca chei pentru robusteză în template (dict lookups)
        breakdown = []  # list of tuples (child_id, grandchildren)
        if children:
            grandchildren_by_parent = {
                child.id: request.env["stock.location"].sudo().search([("location_id", "=", child.id)], order="name")
                for child in children
            }
            empty_rs = request.env["stock.location"].sudo()
            breakdown = [(child.id, grandchildren_by_parent.get(child.id, empty_rs)) for child in children]

        return request.render(
            "deltatech_warehouse_map.view_location_generic",
            {
                "location": location,
                "children": children,
                "breakdown": breakdown,
            },
        )

    @http.route("/deltatech/warehouse_map/location_open_quants/<int:loc_id>", type="http", auth="user")
    def location_open_quants(self, loc_id, **kwargs):
        # Afișare generică: pentru o locație selectată, afișează copiii pe linii,
        # iar pentru fiecare copil afișează copiii lui pe o a doua linie (defalcare).
        location = request.env["stock.location"].sudo().browse(loc_id).exists()
        if not location:
            return request.not_found()



        action = request.env["ir.actions.actions"].sudo()._for_xml_id("stock.location_open_quants")
        action["domain"] = [("location_id", "child_of", [location.id])]
        action["context"] = {"search_default_productgroup": 1}
        action["name"] = f"Current Stock in {location.display_name}"

        return action
