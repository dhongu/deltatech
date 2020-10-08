# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64

from odoo import api, fields, models, tools
from odoo.modules import get_module_resource


class PropertyBuilding(models.Model):
    _name = "property.building"
    _description = "Building"
    _inherit = "property.property"

    land_id = fields.Many2one("property.land", string="Land")

    categ_id = fields.Many2one("property.building.categ", string="Category")
    room_ids = fields.One2many("property.room", "building_id", string="Rooms")
    features_ids = fields.One2many("property.features", "building_id", string="Features")

    # administrator_id = fields.Many2one('res.partner', string="Administrator", domain=[('is_company', '=', False)])

    purpose_parent_id = fields.Many2one(
        "property.building.purpose", string="Purpose building", domain=[("parent_id", "=", False)]
    )
    purpose_id = fields.Many2one(
        "property.building.purpose", string="Purpose building for", domain="[('parent_id','=',purpose_parent_id)]"
    )

    data_pif = fields.Date(string="Data PIF")

    parking_space = fields.Integer(string="Parking Space", help="Parking Space Available")
    occupants = fields.Integer(string="Occupants")
    occupied_date = fields.Date(string="Date Occupied")
    finished = fields.Boolean()

    roof_structure = fields.Selection(
        [
            ("tile", "wood roofing structure, tile roofing"),
            ("metal", "wood structure, sheet metal cover"),
            ("asbestos", "wood structure, roofing asbestos cement"),
            ("bituminous", "terrace structure, bituminous membrane cover"),
        ],
        string="Roof Structure",
    )

    surface_built = fields.Float(string="Surface built")  # Sc
    surface_unfolded = fields.Float(string="Surface unfolded")  # Sd
    surface_terraces = fields.Float(string="Surface terraces")  # Ster

    surface_flameproof = fields.Float(string="Flameproof surface")  # Sig

    surface_useful = fields.Float(
        string="Useful surface",
        help="∑ Sbir + Scc +  Slb + Sit + Sgar + Smag + Slog + Sarh + Sves + Steh ",
        # compute="_compute_all_surface",
        store=True,
    )  # Su

    surface_common = fields.Float(
        string="Common surface",
        help="The common area of the building ∑ Ssed + Shol + Scs + Sof + Sgrs + Sacc",
        # compute="_compute_all_surface",
        store=True,
    )  # Scc

    surface_office = fields.Float(string="Surface office", compute="_compute_all_surface", store=True)  # Sbir
    surface_living = fields.Float(string="Surface living", compute="_compute_all_surface", store=True)  #
    surface_bedroom = fields.Float(string="Surface bedroom", compute="_compute_all_surface", store=True)  #

    surface_meeting = fields.Float(string="Surface meeting", compute="_compute_all_surface", store=True)  # Ssed
    surface_lobby = fields.Float(string="Surface lobby", compute="_compute_all_surface", store=True)  # Shol
    surface_staircase = fields.Float(string="Surface staircase", compute="_compute_all_surface", store=True)  # Scs
    surface_kitchen = fields.Float(string="Surface kitchen", compute="_compute_all_surface", store=True)  # Sof
    surface_sanitary = fields.Float(string="Surface sanitary", compute="_compute_all_surface", store=True)  # Sgrs

    surface_laboratory = fields.Float(string="Surface laboratory", compute="_compute_all_surface", store=True)  # Slb
    surface_it_endowments = fields.Float(
        string="Surface IT endowments", compute="_compute_all_surface", store=True
    )  # Sit
    surface_garage = fields.Float(string="Surface garage", compute="_compute_all_surface", store=True)  # Sgar
    surface_warehouse = fields.Float(string="Surface warehouse", compute="_compute_all_surface", store=True)  # Smag
    surface_log_warehouse = fields.Float(
        string="Surface logistic warehouse", compute="_compute_all_surface", store=True
    )  # Slog
    surface_archive = fields.Float(string="Surface archive", compute="_compute_all_surface", store=True)  # Sarh
    surface_cloakroom = fields.Float(string="Surface cloakroom", compute="_compute_all_surface", store=True)  # Sves
    surface_premises = fields.Float(string="Surface premises", compute="_compute_all_surface", store=True)  # Steh
    surface_access = fields.Float(string="Surface access", compute="_compute_all_surface", store=True)  # Sacc

    surface_cleaned_adm = fields.Float(
        string="Surface cleaned administratively", compute="_compute_all_surface", store=True
    )  # Sca
    surface_cleaned_ind = fields.Float(
        string="Surface cleaned industrial", compute="_compute_all_surface", store=True
    )  # Sci

    surface_cleaned_ext = fields.Float(string="External surface cleaned")  # Scext
    surface_cleaned_tot = fields.Float(
        string="Total surface cleaned", compute="_compute_all_surface", store=True
    )  # Stc

    surface_derating_ext = fields.Float(string="Surface derating external")  # Sdze
    surface_derating_int = fields.Float(
        string="Surface derating internal", compute="_compute_all_surface", store=True  # Sdzi
    )  # Sdzt = ∑ Sdzi+Sdze
    surface_derating = fields.Float(
        string="Total surface derating", compute="_compute_all_surface", store=True
    )  # Sdzt = ∑ Sdzi+Sdze

    surface_disinsection = fields.Float(
        string="Area of disinsection", compute="_compute_surface_disinsection", store=True
    )  # Sds

    surface_cleaning_carpet = fields.Float(
        string="Surface cleaning Carpet", compute="_compute_cleaning_floor", store=True
    )  # Sctextil
    surface_cleaning_linoleum = fields.Float(
        string="Surface cleaning Linoleum", compute="_compute_cleaning_floor", store=True
    )  # Scgresie
    surface_cleaning_wood = fields.Float(
        string="Surface cleaning Wood", compute="_compute_cleaning_floor", store=True
    )  # Scpodea

    surface_cleaning_doors = fields.Float(
        string="Surface cleaning doors", compute="_compute_cleaning_doors", store=True
    )  # Scusi
    surface_cleaning_windows = fields.Float(
        string="Surface cleaning window", compute="_compute_cleaning_windows", store=True
    )  # Scgeam

    maintenance_team_type = fields.Selection([("internal", "Internal"), ("external", "external")])
    verification_date = fields.Date()
    verification_note = fields.Char()

    history_ids = fields.One2many("building.history", "building_id")
    market_rent_value = fields.Monetary()
    reevaluation_date = fields.Date()
    reevaluation_value = fields.Monetary()
    monthly_average_winter = fields.Monetary("Monthly utilities average - winter")
    monthly_average_summer = fields.Monetary("Monthly utilities average - summer")
    furniture_at_occupation = fields.Selection([("Full", "Full"), ("Semi", "Semi"), ("None", "None")])
    martket_similar_value = fields.Monetary("Market value for similar property")

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get("import_file"):
            self._check_import_consistency(vals_list)
        for vals in vals_list:
            if not vals.get("image"):
                vals["image"] = self._get_default_image()
            tools.image_resize_images(vals, sizes={"image": (1024, None)})

        buildings = super(PropertyBuilding, self).create(vals_list)

        return buildings

    @api.model
    def _get_default_image(self):
        if self._context.get("install_mode"):
            return False

        colorize, img_path, image = False, False, False

        img_path = get_module_resource("deltatech_property", "static/src/img", "building.png")
        colorize = True

        if img_path:
            with open(img_path, "rb") as f:
                image = f.read()
        if image and colorize:
            image = tools.image_colorize(image)

        return tools.image_resize_image_big(base64.b64encode(image))

    @api.onchange("purpose_parent_id")
    def onchange_purpose_parent_id(self):
        if self.purpose_id.parent_id != self.purpose_parent_id:
            self.purpose_id = False

        if self.purpose_parent_id:
            return {"domain": {"purpose_id": [("parent_id", "=", self.purpose_parent_id.id)]}}
        else:
            return {"domain": {"purpose_id": []}}

    @api.onchange("purpose_id")
    def onchange_purpose_id(self):
        self.purpose_parent_id = self.purpose_id.parent_id

    @api.depends("room_ids.surface_cleaning_floor", "room_ids.floor_type")
    def _compute_cleaning_floor(self):
        surface_cleaning_carpet = 0.0
        surface_cleaning_linoleum = 0.0
        surface_cleaning_wood = 0.0

        for room in self.room_ids:
            if room.floor_type == "c":
                surface_cleaning_carpet += room.surface_cleaning_floor
            if room.floor_type == "l":
                surface_cleaning_linoleum += room.surface_cleaning_floor
            if room.floor_type == "w":
                surface_cleaning_wood += room.surface_cleaning_floor

        self.surface_cleaning_carpet = surface_cleaning_carpet
        self.surface_cleaning_linoleum = surface_cleaning_linoleum
        self.surface_cleaning_wood = surface_cleaning_wood

    @api.depends("room_ids.surface_cleaning_windows")
    def _compute_cleaning_windows(self):
        surface_cleaning_windows = 0.0
        for room in self.room_ids:
            surface_cleaning_windows += room.surface_cleaning_windows
        self.surface_cleaning_windows = surface_cleaning_windows

    @api.depends("room_ids.surface_cleaning_doors")
    def _compute_cleaning_doors(self):
        surface_cleaning_doors = 0.0
        for room in self.room_ids:
            surface_cleaning_doors += room.surface_cleaning_doors
        self.surface_cleaning_doors = surface_cleaning_doors

    @api.depends("room_ids.surface_disinsection")
    def _compute_surface_disinsection(self):
        surface_disinsection = 0.0
        for room in self.room_ids:
            surface_disinsection += room.surface_disinsection
        self.surface_disinsection = surface_disinsection

    @api.depends("room_ids.surface", "surface_terraces", "surface_cleaned_ext", "surface_derating_ext")
    def _compute_all_surface(self):
        # TODO: de refacut calculele dinamic, in functie de room.usage
        pass

        # for building in self:
        #     surface = {
        #         "office": 0.0,
        #         "living": 0.0,
        #         "bedroom": 0.0,
        #         "meeting": 0.0,
        #         "lobby": 0.0,
        #         "staircase": 0.0,
        #         "kitchen": 0.0,
        #         "sanitary": 0.0,
        #         "laboratory": 0.0,
        #         "it_endowments": 0.0,
        #         "garage": 0.0,
        #         "warehouse": 0.0,
        #         "log_warehouse": 0.0,
        #         "archive": 0.0,
        #         "cloakroom": 0.0,
        #         "premises": 0.0,
        #         "access": 0.0,
        #     }
        #     # for room in building.room_ids:
        #     #     surface[room.usage] += room.surface
        #
        #     building.surface_office = surface["office"]
        #     building.surface_living = surface["living"]
        #     building.surface_bedroom = surface["bedroom"]
        #
        #     building.surface_meeting = surface["meeting"]
        #     building.surface_lobby = surface["lobby"]
        #     building.surface_staircase = surface["staircase"]
        #     building.surface_kitchen = surface["kitchen"]
        #     building.surface_sanitary = surface["sanitary"]
        #     building.surface_laboratory = surface["laboratory"]
        #     building.surface_it_endowments = surface["it_endowments"]
        #     building.surface_garage = surface["garage"]
        #     building.surface_warehouse = surface["warehouse"]
        #     building.surface_log_warehouse = surface["log_warehouse"]
        #     building.surface_archive = surface["archive"]
        #     building.surface_cloakroom = surface["cloakroom"]
        #     building.surface_premises = surface["premises"]
        #     building.surface_access = surface["access"]
        #
        #     building.surface_common = (
        #         surface["meeting"]
        #         + surface["lobby"]
        #         + surface["staircase"]
        #         + surface["kitchen"]
        #         + surface["sanitary"]
        #         + surface["access"]
        #     )
        #
        #     building.surface_useful = (
        #         surface["office"]
        #         + surface["living"]
        #         + surface["bedroom"]
        #         + building.surface_common
        #         + surface["laboratory"]
        #         + surface["it_endowments"]
        #         + surface["garage"]
        #         + surface["warehouse"]
        #         + surface["log_warehouse"]
        #         + surface["archive"]
        #         + surface["cloakroom"]
        #         + surface["premises"]
        #     )
        #
        #     building.surface_cleaned_adm = (
        #         building.surface_common + surface["office"] + surface["living"] + surface["bedroom"]
        #     )
        #     building.surface_cleaned_ind = surface["garage"] + surface["cloakroom"] + building.surface_terraces
        #
        #     building.surface_cleaned_tot = (
        #         building.surface_cleaned_adm + building.surface_cleaned_ind + building.surface_cleaned_ext
        #     )
        #
        #     building.surface_derating_int = building.surface_useful
        #     building.surface_derating = building.surface_derating_ext + building.surface_derating_int


class PropertyFeatures(models.Model):
    _name = "property.features"
    _description = "Features"

    building_id = fields.Many2one("property.building", string="Building", required=True)
    categ = fields.Selection(
        [
            ("E", "Extinguishers"),
            ("H", "Hydrants"),
            ("M", "Medical kits"),
            ("A", "Air conditioning equipment"),
            ("D", "Deflector"),
            ("W", "Water dispensers"),
            ("L", "Lightning discharger"),
            ("G", "Grounding socket "),
            ("S", "Signage"),
        ],
        string="Features",
    )

    number = fields.Integer()
    observation = fields.Char()


class BuildingHistory(models.Model):
    _name = "building.history"
    _description = "Building History"

    building_id = fields.Many2one("property.building", string="Building", required=True, ondelete="cascade")
    tenant_id = fields.Many2one("res.partner", string="Tenant")
    from_date = fields.Date(string="From date")
    to_date = fields.Date(string="To date")
    note = fields.Char()
