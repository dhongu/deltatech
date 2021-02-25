odoo.define("deltatech_sale_qty_available.QtyAvailableWidget", function (require) {
    "use strict";

    var core = require("web.core");
    var QWeb = core.qweb;

    var Widget = require("web.Widget");
    // Var Context = require("web.Context");
    // var data_manager = require("web.data_manager");
    var widget_registry = require("web.widget_registry");
    var field_registry = require("web.field_registry");

    // Var config = require("web.config");

    var _t = core._t;
    // Var time = require("web.time");
    var AbstractField = require("web.AbstractField");
    // Var ListRenderer = require("web.ListRenderer");

    var QtyAvailableField = AbstractField.extend({
        template: "deltatech_sale_qty_available.qtyAvailable",
        events: _.extend({}, Widget.prototype.events, {
            "click .fa-info-circle": "_onClickButton",
        }),

        init: function () {
            this._super.apply(this, arguments);
            this.data = this.record.data;
        },
        _render: function () {
            var self = this;
            self._setPopOver();
        },

        _setPopOver: function () {
            // Var self = this;
            this.data = this.record.data;
            if (!this.data.product_id) {
                return;
            }
            var $content = $(
                QWeb.render("deltatech_sale_qty_available.QtyDetailPopOver", {
                    data: this.data,
                })
            );

            var options = {
                content: $content,
                html: true,
                placement: "left",
                title: _t("Availability"),
                trigger: "focus",
                delay: {show: 0, hide: 100},
            };
            this.$el.popover(options);
        },
        _onClickButton: function () {
            // We add the property special click on the widget link.
            // This hack allows us to trigger the popover (see _setPopOver) without
            // triggering the _onRowClicked that opens the order line form view.
            this.$el.find(".fa-info-circle").prop("special_click", true);
        },
    });

    var QtyAvailableWidget = Widget.extend({
        template: "deltatech_sale_qty_available.qtyAvailable",
        events: _.extend({}, Widget.prototype.events, {
            "click .fa-info-circle": "_onClickButton",
        }),

        /**
         * @override
         * @param {Widget|null} parent
         * @param {Object} params
         */
        init: function (parent, params) {
            this.data = params.data;
            this._super(parent);
        },

        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._setPopOver();
            });
        },

        updateState: function (state) {
            this.$el.popover("dispose");
            var candidate = state.data[this.getParent().currentRow];
            if (candidate) {
                this.data = candidate.data;
                this.renderElement();
                this._setPopOver();
            }
        },
        // --------------------------------------------------------------------------
        // Private
        // --------------------------------------------------------------------------
        /**
         * Set a bootstrap popover on the current QtyAtDate widget that display available
         * quantity.
         */
        _setPopOver: function () {
            // Var $content;
            // var options;
            // var self = this;
            if (!this.data.product_id) {
                return;
            }
            var $content = $(
                QWeb.render("deltatech_sale_qty_available.QtyDetailPopOver", {
                    data: this.data,
                })
            );

            var options = {
                content: $content,
                html: true,
                placement: "left",
                title: _t("Availability"),
                trigger: "focus",
                delay: {show: 0, hide: 100},
            };
            this.$el.popover(options);
        },

        // --------------------------------------------------------------------------
        // Handlers
        // --------------------------------------------------------------------------
        _onClickButton: function () {
            // We add the property special click on the widget link.
            // This hack allows us to trigger the popover (see _setPopOver) without
            // triggering the _onRowClicked that opens the order line form view.
            this.$el.find(".fa-info-circle").prop("special_click", true);
        },
    });

    widget_registry.add("qty_available_widget", QtyAvailableWidget);

    field_registry.add("qty_available", QtyAvailableField);

    return QtyAvailableWidget;
});
