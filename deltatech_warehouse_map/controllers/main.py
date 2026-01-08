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
                "children": stock.child_ids if stock else [],
            },
        )

    @http.route("/deltatech/warehouse_map/location/<int:loc_id>", type="http", auth="user")
    def view_location(self, loc_id, **kwargs):
        # Afișare generică: pentru o locație selectată, afișează copiii pe linii,
        # iar pentru fiecare copil afișează copiii lui pe o a doua linie (defalcare).
        location = request.env["stock.location"].sudo().browse(loc_id).exists()
        if not location:
            return request.not_found()

        # Pre-fetch children
        children = request.env["stock.location"].sudo().search([("location_id", "=", location.id)])

        quants = request.env["stock.quant"].sudo()
        if not children:
            quants = request.env["stock.quant"].sudo().search([("location_id", "=", location.id), ("quantity", ">", 0)])
        else:
            # Pre-fetch fields to avoid multiple queries in template
            children.read(["name", "display_name", "current_products", "max_products", "occupancy_ratio", "child_ids"])

        return request.render(
            "deltatech_warehouse_map.view_location_generic",
            {
                "location": location,
                "children": children,
                "quants": quants,
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
