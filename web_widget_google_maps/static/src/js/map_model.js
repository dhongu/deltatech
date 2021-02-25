odoo.define("web_map.MapModel", function (require) {
    "use strict";
    var AbstractModel = require("web.AbstractModel");
    var session = require("web.session");
    var core = require("web.core");
    var _t = core._t;
    var MapModel = AbstractModel.extend({
        // -----------------------------------------------------------------------------------
        // Public
        // ----------------------------------------------------------------------------------
        init: function () {
            this._super.apply(this, arguments);
            this.data = {};
            this.data.mapBoxToken = session.map_box_token;
        },

        get: function () {
            return this.data;
        },

        load: function (params) {
            this.data.count = 0;
            this.data.offset = 0;
            this.data.limit = 80;
            this.partnerToCache = [];
            this.partnerIds = [];
            this.resPartnerField = params.resPartnerField;
            this.model = params.modelName;
            this.context = params.context;
            this.fields = params.fieldNames;
            this.domain = params.domain;
            this.params = params;
            this.orderBy = params.orderBy;
            this.routing = params.routing;
            this.numberOfLocatedRecords = 0;
            return this._fetchData();
        },

        reload: function (handle, params) {
            var options = params || {};
            this.partnerToCache = [];
            this.partnerIds = [];
            this.numberOfLocatedRecords = 0;
            if (options.domain !== undefined) {
                this.domain = options.domain;
            }
            if (options.limit !== undefined) {
                this.data.limit = options.limit;
            }
            if (options.offset !== undefined) {
                this.data.offset = options.offset;
            }
            return this._fetchData();
        },

        //* **************************************************************************************
        // Private
        //* **************************************************************************************

        /**
         * handles the case of an empty map
         * handles the case where the model is res_partner
         * fetches the records according to the model given in the arch.
         * if the records has no partner_id field it is sliced from the array
         * @private
         * @returns {Promise}
         */
        _fetchData: async function () {
            // Case of empty map
            if (!this.resPartnerField) {
                this.data.records = [];
                this.data.route = {routes: []};
                return;
            }
            var results = await this._fetchRecordData();
            this.data.records = results.records;
            this.data.count = results.length;
            this.partnerIds = [];
            if (this.model === "res.partner" && this.resPartnerField === "id") {
                this.data.records.forEach((record) => {
                    this.partnerIds.push(record.id);
                    record.partner_id = [record.id];
                });
            } else {
                this._fillPartnerIds(this.data.records);
            }

            this.partnerIds = _.uniq(this.partnerIds);
            return this._partnerFetching(this.partnerIds);
        },

        /**
         * Fetches the partner which ids are contained in the the array partnerids
         * if the token is set it uses the mapBoxApi to fetch address and route
         * if not is uses the openstreetmap api to fetch the address
         * @private
         * @param {Number[]} partnerIds this array contains the ids from the partner that are linked to records
         * @returns {Promise}
         */
        _partnerFetching: async function (partnerIds) {
            this.data.partners = partnerIds.length ? await this._fetchRecordsPartner(partnerIds) : [];
            if (this.data.mapBoxToken) {
                return this._maxBoxAPI()
                    .then(() => {
                        this._writeCoordinatesUsers();
                    })
                    .catch((err) => {
                        this._mapBoxErrorHandling(err);
                        this.data.mapBoxToken = "";
                        return this._openStreetMapAPI();
                    });
            }
            return this._openStreetMapAPI().then(() => {
                this._writeCoordinatesUsers();
            });
        },

        /**
         * Handles the displaying of error message according to the error
         * @param {Object} err contains the error returned by the requests
         * @param {Number} err.status contains the status_code of the failed http request
         */
        _mapBoxErrorHandling: function (err) {
            switch (err.status) {
                case 401:
                    this.do_warn(
                        _t("Token invalid"),
                        _t("The view has switched to another provider but functionalities will be limited")
                    );
                    break;
                case 403:
                    this.do_warn(
                        _t("Unauthorized connection"),
                        _t("The view has switched to another provider but functionalities will be limited")
                    );
                    break;
                case 500:
                    this.do_warn(
                        _t("MapBox servers unreachable"),
                        _t("The view has switched to another provider but functionalities will be limited")
                    );
            }
        },

        /**
         * Adds the corresponding partner to a record
         * @private
         */
        _addPartnerToRecord: function () {
            this.data.records.forEach((record) => {
                this.data.partners.forEach((partner) => {
                    var recordPartnerId = "";
                    if (this.model === "res.partner" && this.resPartnerField === "id") {
                        recordPartnerId = record.id;
                    } else {
                        recordPartnerId = record[this.resPartnerField][0];
                    }

                    if (recordPartnerId === partner.id) {
                        record.partner = partner;
                        this.numberOfLocatedRecords++;
                    }
                });
            });
            // }
        },

        /**
         * Handles the case where the selected api is open street map
         * Iterates on all the partners and fetches their coordinates when they're not set.
         * @private
         * @returns {Promise[]} returns an array of promise that fetches the coordinates from the address
         */
        _openStreetMapAPI: function () {
            var self = this;
            var promises = [];
            this.data.partners.forEach((partner) => {
                if (partner.contact_address_complete && (!partner.partner_latitude || !partner.partner_longitude)) {
                    promises.push(
                        self._fetchCoordinatesFromAddressOSM(partner).then(function (coordinates) {
                            if (coordinates.length) {
                                partner.partner_longitude = coordinates[0].lon;
                                partner.partner_latitude = coordinates[0].lat;
                                self.partnerToCache.push(partner);
                            }
                        })
                    );
                } else if (!this._checkCoordinatesValidity(partner)) {
                    partner.partner_latitude = undefined;
                    partner.partner_longitude = undefined;
                }
            });
            return Promise.all(promises).then(function () {
                self._addPartnerToRecord();
            });
        },

        _maxBoxAPI: function () {
            var self = this;
            var promises = [];
            this.data.partners.forEach((partner) => {
                if (partner.contact_address_complete && (!partner.partner_latitude || !partner.partner_longitude)) {
                    promises.push(
                        self._fetchCoordinatesFromAddressMB(partner).then(function (coordinates) {
                            if (coordinates.features.length) {
                                partner.partner_longitude = coordinates.features[0].geometry.coordinates[0];
                                partner.partner_latitude = coordinates.features[0].geometry.coordinates[1];
                                self.partnerToCache.push(partner);
                            }
                        })
                    );
                } else if (!this._checkCoordinatesValidity(partner)) {
                    partner.partner_latitude = undefined;
                    partner.partner_longitude = undefined;
                }
            });
            return Promise.all(promises).then(function () {
                self._addPartnerToRecord();
                self.data.route = {routes: []};
                if (self.numberOfLocatedRecords > 1 && self.routing) {
                    return self._fetchRoute().then(function (routeResult) {
                        self.data.route = routeResult;
                    });
                }
                return Promise.resolve();
            });
        },

        /**
         * @param {Object[]} records the records that are going to be filtered
         * @returns {Object[]} Array of records that contains a partner_id
         */
        _fillPartnerIds: function (records) {
            return records.forEach((record) => {
                if (record[this.resPartnerField]) {
                    this.partnerIds.push(record[this.resPartnerField][0]);
                }
            });
        },

        /**
         * The partner's coordinates should be between -90 <= latitude <= 90 and -180 <= longitude <= 180
         *
         * @param {Object} partner
         * @param {float} partner.partner_latitude latitude of the partner
         * @param {float} partner.partner_longitude longitude of the partner
         * @returns {Boolean}
         * @private
         */
        _checkCoordinatesValidity: function (partner) {
            if (
                partner.partner_latitude &&
                partner.partner_longitude &&
                partner.partner_latitude >= -90 &&
                partner.partner_latitude <= 90 &&
                partner.partner_longitude >= -180 &&
                partner.partner_longitude <= 180
            ) {
                return true;
            }
            return false;
        },

        /**
         * @private
         * @param {Number[]} ids contains the ids from the partners
         * @returns {Promise}
         */
        _fetchRecordsPartner: function (ids) {
            return this._rpc({
                model: "res.partner",
                method: "search_read",
                fields: ["contact_address_complete", "partner_latitude", "partner_longitude"],
                domain: [
                    ["contact_address_complete", "!=", "False"],
                    ["id", "in", ids],
                ],
            });
        },

        /**
         * This function convert the addresses to coordinates using the mapbox API.
         * @private
         * @param {Object} record this object contains the record fetched from the database.
         * @returns {Promise<result>} result.query contains the query the the api received
         * result.features contains results in descendant order of relevance
         */
        _fetchCoordinatesFromAddressMB: function (record) {
            var encodedUrl =
                "https://api.mapbox.com/geocoding/v5/mapbox.places/" +
                encodeURIComponent(record.contact_address_complete) +
                ".json?access_token=" +
                this.data.mapBoxToken +
                "&cachebuster=1552314159970&autocomplete=true";
            return new Promise(function (resolve, reject) {
                $.ajax({
                    url: encodedUrl,
                    method: "GET",
                })
                    .then(resolve)
                    .catch(reject);
            });
        },

        /**
         * This function convert the addresses to coordinates using the openStreetMap api.
         * @private
         * @param {Object} record this object contains the record fetched from the database.
         * @returns {Promise<result>} result is an array that contains the result in descendant order of relevance
         * result[i].lat is the latitude of the converted address
         * result[i].lon is the longitude of the converted address
         * result[i].importance is a float that the relevance of the result the closer the float is to one the best it is.
         */
        _fetchCoordinatesFromAddressOSM: function (record) {
            var contact_address_complete = record.contact_address_complete.replace("/", " ");
            var encodedUrl =
                "https://nominatim.openstreetmap.org/search/" +
                encodeURIComponent(contact_address_complete) +
                "?format=jsonv2";
            return new Promise(function (resolve, reject) {
                $.ajax({
                    url: encodedUrl,
                    method: "GET",
                })
                    .then(resolve)
                    .catch(reject);
            });
        },

        _writeCoordinatesUsers: function () {
            var self = this;
            if (this.partnerToCache.length) {
                this._rpc({
                    model: "res.partner",
                    method: "update_latitude_longitude",
                    context: self.context,
                    args: [this.partnerToCache],
                });
                this.partnerToCache = [];
            }
        },

        /**
         * Fetch the records for a given model
         * @private
         * @returns {Promise<results>}
         */
        _fetchRecordData: function () {
            return this._rpc({
                route: "/web/dataset/search_read",
                model: this.model,
                context: this.context,
                fields: this.fields,
                domain: this.domain,
                orderBy: this.orderBy,
                limit: this.data.limit,
                offset: this.data.offset,
            });
        },

        /**
         * Fetch the route from the mapbox api
         * @private
         * @returns {Promise<results>}
         * results.geometry.legs[i] contains one leg (i.e: the trip between two markers).
         * results.geometry.legs[i].steps contains the sets of coordinates to follow to reach a point from an other.
         * results.geometry.legs[i].distance: the distance in meters to reach the destination
         * results.geometry.legs[i].duration the duration of the leg
         * results.geometry.coordinates contains the sets of coordinates to go from the first to the last marker without the notion of waypoint
         */
        _fetchRoute: function () {
            var coordinatesParam = "";
            this.data.records.forEach(function (record) {
                if (record.partner.partner_latitude && record.partner.partner_longitude) {
                    coordinatesParam += record.partner.partner_longitude + "," + record.partner.partner_latitude + ";";
                }
            });
            coordinatesParam = coordinatesParam.slice(0, -1);
            var encodedUrl =
                "https://api.mapbox.com/directions/v5/mapbox/driving/" +
                encodeURIComponent(coordinatesParam) +
                "?access_token=" +
                this.data.mapBoxToken +
                "&steps=true&geometries=geojson";
            return new Promise(function (resolve, reject) {
                $.ajax({
                    url: encodedUrl,
                    method: "GET",
                })
                    .then(resolve)
                    .catch(reject);
            });
        },
    });
    return MapModel;
});
