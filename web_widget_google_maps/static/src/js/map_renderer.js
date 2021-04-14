odoo.define("web_map.MapRenderer", function (require) {
    "use strict";
    var core = require("web.core");
    var AbstractRenderer = require("web.AbstractRenderer");
    var qweb = core.qweb;

    var MapRenderer = AbstractRenderer.extend({
        className: "o_map_view row no-gutters",
        // ---------------------------------------------------------------------------
        // Public
        // --------------------------------------------------------------------------

        init: function (parent, state, params) {
            this._super.apply(this, arguments);
            this.fieldsMarkerPopup = params.fieldNamesMarkerPopup;
            this.numbering = params.numbering;
            this.hasFormView = params.hasFormView;
            this.defaultOrder = params.defaultOrder;

            this.isInDom = false;
            this.mapIsInit = false;
            this.markers = [];
            this.polylines = [];

            this.panelTitle = params.panelTitle;

            this.mapBoxToken = state.mapBoxToken;
            this.apiTilesRoute = "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png";
            if (this.mapBoxToken) {
                this.apiTilesRoute = "https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}";
            }
        },

        /*
         * Called each time the renderer is attached into the DOM.
         */
        on_attach_callback: function () {
            this.isInDom = true;
            this._initializeMap();
            var initialCoord = this._getLatLng();
            if (initialCoord) {
                this.leafletMap.fitBounds(initialCoord);
            } else {
                this.leafletMap.fitWorld();
            }
            this._addMakers(this.state.records);
            this._addRoutes(this.state.route);

            this._addPinList();
        },

        /*
         *Called each time the renderer is detached from the DOM.
         */
        on_detach_callback: function () {
            this.isInDom = false;
        },

        /**
         * @override
         * manually destroys the handlers to avoid memory leaks
         * destroys manually the map
         */
        destroy: function () {
            this.markers.forEach(function (marker) {
                marker.off("click");
            });
            this.polylines.forEach(function (polyline) {
                polyline.off("click");
            });
            this.leafletMap.remove();
            return this._super.apply(this, arguments);
        },

        // --------------------------------------------------------------------------------------------------------------------
        // Private
        // --------------------------------------------------------------------------------------------------------------------

        /**
         *Initialize the map, if there is located records the map is set to fit them at the maximum zoom level possible
         *If there is no located record the map will fit the world.
         *The function also fetches the tiles
         *The maxZoom property correspond to the maximum zoom level of the map. The greater the number,
         *the greater the user will be able to zoom.
         *@private
         */
        _initializeMap: function () {
            if (this.mapIsInit) {
                return;
            }
            this.mapIsInit = true;
            var mapContainer = document.createElement("div");
            mapContainer.classList.add("o_map_container", "col-md-12", "col-lg-10");
            this.el.appendChild(mapContainer);
            this.leafletMap = google.map(mapContainer, {
                maxBounds: [google.latLng(180, -180), google.latLng(-180, 180)],
            });
            google
                .tileLayer(this.apiTilesRoute, {
                    attribution:
                        'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
                    minZoom: 2,
                    maxZoom: 19,
                    id: "mapbox.streets",
                    accessToken: this.mapBoxToken,
                })
                .addTo(this.leafletMap);
        },

        /**
         *Creates an array of latLng objects if there is located records
         *
         * @private
         * @returns {latLngBounds|Boolean} objects containing the coordinates that allows all the records to be shown on the map or returns false if the records does not contain any located record
         */
        _getLatLng: function () {
            var tabLatLng = [];
            this.state.records.forEach(function (record) {
                if (record.partner && record.partner.partner_latitude && record.partner.partner_longitude) {
                    tabLatLng.push(google.latLng(record.partner.partner_latitude, record.partner.partner_longitude));
                }
            });
            if (!tabLatLng.length) {
                return false;
            }
            return google.latLngBounds(tabLatLng);
        },

        /**
         * @private
         * @param {Object} record is a record from the database
         * @param {Object} fields is an object that contain all the field that are going to be shown in the view
         * @returns {Object} field: contains the value of the field and string contains the value of the xml's string attribute
         */
        _getMarkerPopupFields: function (record, fields) {
            var fieldsView = [];
            fields.forEach(function (field) {
                if (record[field.fieldName]) {
                    if (record[field.fieldName] instanceof Array) {
                        fieldsView.push({field: record[field.fieldName][1], string: field.string});
                    } else {
                        fieldsView.push({field: record[field.fieldName], string: field.string});
                    }
                }
            });
            return fieldsView;
        },

        /**
         * If there's located records, adds the corresponding marker on the map
         * Binds events to the created markers
         * @private
         * @param {Array} records array that contains the records that needs to be displayed on the map
         * @param {Object} records.partner is the partner linked to the record
         * @param {float} records.partner.partner_latitude latitude of the partner and thus of the record
         * @param {float} records.partner.partner_longitude longitude of the partner and thus of the record
         */
        _addMakers: function (records) {
            var self = this;
            this._removeMakers();
            records.forEach(function (record) {
                if (record.partner && record.partner.partner_latitude && record.partner.partner_longitude) {
                    var popup = {};
                    popup.records = self._getMarkerPopupFields(record, self.fieldsMarkerPopup);
                    popup.url =
                        "https://www.google.com/maps/dir/?api=1&destination=" +
                        record.partner.partner_latitude +
                        "," +
                        record.partner.partner_longitude;
                    var $popup = $(qweb.render("map-popup", {records: popup}));
                    var openButton = $popup.find("button.btn.btn-primary.edit")[0];
                    if (self.hasFormView) {
                        openButton.onclick = function () {
                            self.trigger_up("open_clicked", {id: record.id});
                        };
                    } else {
                        openButton.remove();
                    }

                    var marker = {};
                    var offset = {};
                    if (self.numbering) {
                        var number = google.divIcon({
                            className: "o_numbered_marker",
                            html: '<p class ="o_number_icon">' + (self.state.records.indexOf(record) + 1) + "</p>",
                        });
                        marker = google.marker([record.partner.partner_latitude, record.partner.partner_longitude], {
                            icon: number,
                        });
                        offset = new google.Point(0, -35);
                    } else {
                        marker = google.marker([record.partner.partner_latitude, record.partner.partner_longitude]);
                        offset = new google.Point(0, 0);
                    }
                    marker.addTo(self.leafletMap).bindPopup(
                        function () {
                            var divPopup = document.createElement("div");
                            $popup.each(function (i, element) {
                                divPopup.appendChild(element);
                            });
                            return divPopup;
                        },
                        {offset: offset}
                    );
                    self.markers.push(marker);
                }
            });
        },
        /**
         * Adds the list of records to the dom
         * @private
         */
        _addPinList: function () {
            this.$pinList = $(qweb.render("MapView.pinlist", {widget: this}));
            var $container = this.$el.find(".o_pin_list_container");
            if ($container.length) {
                $container.replaceWith(this.$pinList);
            } else {
                this.$el.append(this.$pinList);
            }

            this.$(".o_pin_list_container li a").on("click", this._centerAndOpenPin.bind(this));
        },

        /**
         * If there is computed routes, create polylines and add them to the map.
         * each element of this.state.route[0].legs array represent the route between two waypoints thus each of these must be a polyline
         * @private
         * @param {Object} route contains the data that allows to draw the rout between the records.
         */
        _addRoutes: function (route) {
            this._removeRoutes();
            var self = this;
            if (!this.mapBoxToken || !route.routes.length) {
                return;
            }

            route.routes[0].legs.forEach(function (leg) {
                var latLngs = [];
                leg.steps.forEach(function (step) {
                    step.geometry.coordinates.forEach(function (coordinate) {
                        latLngs.push(google.latLng(coordinate[1], coordinate[0]));
                    });
                });

                var polyline = google
                    .polyline(latLngs, {
                        color: "blue",
                        weight: 5,
                        opacity: 0.3,
                    })
                    .addTo(self.leafletMap);

                polyline.on("click", function () {
                    self.polylines.forEach(function (poly) {
                        poly.setStyle({color: "blue", opacity: 0.3});
                    });
                    this.setStyle({color: "darkblue", opacity: 1.0});
                    this.bringToFront();
                });
                self.polylines.push(polyline);
            });
        },

        /**
         * Center the map on a certain pin and open the popup linked to it
         *
         * @param {MouseEvent} ev
         * @param {Number} ev.target.dataset.lat the latitude to pass leaflet
         * @param {Number} ev.target.dataset.lng the longitude to pass leaflet
         * @private
         */
        _centerAndOpenPin: function (ev) {
            ev.preventDefault();
            this.leafletMap.panTo(ev.target.dataset, {animate: true});
            var marker = this.markers.find((m) => {
                return m._latlng.lat === ev.target.dataset.lat && m._latlng.lng === ev.target.dataset.lng;
            });
            if (marker) {
                marker.openPopup();
            }
        },

        /**
         * Remove the markers from the map and empties the markers array
         * @private
         */
        _removeMakers: function () {
            var self = this;
            this.markers.forEach(function (marker) {
                self.leafletMap.removeLayer(marker);
            });
            this.markers = [];
        },

        /**
         * Remove the routes from the map and empties the the polyline array
         * @private
         */
        _removeRoutes: function () {
            var self = this;
            this.polylines.forEach(function (polyline) {
                self.leafletMap.removeLayer(polyline);
            });
            this.polylines = [];
        },

        /**
         * Render the map view
         * @private
         * @returns {Promise}
         */
        _render: function () {
            if (this.isInDom) {
                var initialCoord = this._getLatLng();
                if (initialCoord) {
                    this.leafletMap.flyToBounds(initialCoord, {animate: false});
                } else {
                    this.leafletMap.fitWorld();
                }
                this._addMakers(this.state.records);
                this._addRoutes(this.state.route);
                this._addPinList();
            }
            return Promise.resolve();
        },
    });
    return MapRenderer;
});
