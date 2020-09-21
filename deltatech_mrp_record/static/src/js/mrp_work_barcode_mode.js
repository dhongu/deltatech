odoo.define("mrp_work_barcode_mode", function(require) {
    "use strict";

    var core = require("web.core");
    var Widget = require("web.Widget");
    var Session = require("web.session");
    var bus = require("bus.bus").bus;
    var notification = require("web.notification");
    var Dialog = require("web.Dialog");

    var QWeb = core.qweb;
    var _t = core._t;

    var MrpBarcodeMode = Widget.extend({
        custom_events: {
            warning: function(ev) {
                this.notification_manager.warn(ev.data.title, ev.data.message, ev.data.sticky);
            },
            notify: function(ev) {
                this.notification_manager.notify(ev.data.title, ev.data.message, ev.data.sticky);
            },
        },

        events: {
            "click .o_mrp_record_barcode_button_save": function() {
                return self.on_barcode_scanned("#save");
            },
            "click .o_mrp_record_barcode_button_search": function() {
                var self = this;
                var modal = $("#barcodeModal");
                self.barcode = modal.find(".modal-body input").val();
                modal.modal("hide");
                return self.on_barcode_scanned(self.barcode);
            },
        },

        start: function() {
            var self = this;
            self.values = {};
            core.bus.on("barcode_scanned", this, this._onBarcodeScanned);
            self.session = Session;
            self.welcome = true;
            self.statistic = {};
            self.save_buton = false;

            self.notification_manager = new notification.NotificationManager(self);
            self.notification_manager.appendTo(self.$el);

            var def = this._rpc({
                model: "mrp.work.record",
                method: "create",
                args: [{}],
            }).then(function(id) {
                self.mrp_work_record_id = id;
            });

            var def = this._rpc({
                model: "res.company",
                method: "search_read",
                args: [[["id", "=", this.session.company_id]], ["name"]],
            }).then(function(companies) {
                self.company_name = companies[0].name;
                self.company_image_url = self.session.url("/web/image", {
                    model: "res.company",
                    id: self.session.company_id,
                    field: "logo",
                });
                self.$el.html(QWeb.render("MrpWorkBarcodeMode", {widget: self}));
            });

            bus.on("notification", self, self._onNotification);
            bus.update_option("mrp.record", true);
        },

        destroy: function() {
            core.bus.off("barcode_scanned", this, this._onBarcodeScanned);
            clearInterval(this.clock_start);
            this._super.apply(this, arguments);
        },

        _onNotification: function(notifications) {
            for (var notif of notifications) {
                var channel = notif[0],
                    message = notif[1];
                if (channel[1] !== "mrp.record") {
                    return;
                }
                if (message[0] === "refresh") {
                    this.display_workers();
                }
            }
        },

        display_data: function() {
            var self = this;
            if (self.values.work_order_ids) {
                this._rpc({
                    model: "mrp.workorder",
                    method: "read_group",
                    domain: [["id", "in", self.values.work_order_ids]],
                    fields: ["production_id.product_qty", "qty_produced", "duration_expected", "duration"],
                }).then(function(result) {
                    self.statistic = result[0];

                    self.$(".o_mrp_record_barcode_orders_statistic").html(
                        QWeb.render("MrpRecordBarcodeModeStatistic", {widget: self, statistic: self.statistic})
                    );
                });
            }

            if (self.values.work_order_ids) {
                self.welcome = false;
                self.$(".o_mrp_welcome").addClass("hide");
                self.$(".o_mrp_work").removeClass("hide");
                this._rpc({
                    model: "mrp.workorder",
                    method: "search_read",
                    domain: [["id", "in", self.values.work_order_limit_ids]],
                    fields: ["product_id", "qty_production", "qty_produced", "duration_expected", "duration"],
                }).then(function(result) {
                    self.display_orders(result);
                });
            } else {
                self.$(".o_mrp_work").addClass("hide");
                self.$(".o_mrp_welcome").removeClass("hide");
            }
        },

        display_orders: function(work_orders) {
            var self = this;
            self.values.work_orders = work_orders;

            self.$(".o_mrp_record_barcode_orders").html(
                QWeb.render("MrpRecordBarcodeModeOrders", {widget: self, work_orders: work_orders})
            );
            self.display_workers();
        },

        display_workers: function() {
            var self = this;
            if (self.values.work_order_ids) {
                this._rpc({
                    model: "mrp.work.record",
                    method: "get_workers_name",
                    args: [self.values.work_order_ids],
                }).then(function(result) {
                    self.save_buton = false;
                    if (self.statistic.duration > 0 && result.length == 0) {
                        self.save_buton = true;
                    }
                    self.$(".o_mrp_record_barcode_workers").html(
                        QWeb.render("MrpRecordBarcodeModeWorkers", {workers: result, save_buton: self.save_buton})
                    );
                });
            }
        },

        _onBarcodeScanned: function(barcode) {
            this.on_barcode_scanned(barcode);
        },

        on_barcode_scanned: function(barcode, display) {
            var self = this;
            var page = this.$(".o_mrp_record_barcode_mode_container");
            if (barcode == "#save" && !self.save_buton) {
                this.trigger_up("warning", {title: _("Warning"), message: _t("Salvarea nu este posibila")});
                return;
            }
            this._rpc({
                model: "mrp.work.record",
                method: "search_scanned",
                args: [barcode, self.values],
            }).then(function(result) {
                self.values = result;

                if (result.action) {
                    self.do_action(result.action);
                } else if (result.warning) {
                    self.do_warn(_("Warning"), result.warning.message);
                } else if (result.info_message) {
                    self.do_notify(_("Info"), result.info_message);
                }

                if (result.warning) {
                    self.play_sound("error");
                    page.addClass("barcode_not_ok");
                    _.delay(function() {
                        page.removeClass("barcode_not_ok");
                    }, 1000);
                } else {
                    self.play_sound("bell");
                    page.addClass("barcode_ok");
                    _.delay(function() {
                        page.removeClass("barcode_ok");
                    }, 1000);
                }
                self.display_data();
                bus.start_polling();
            });
        },

        play_sound: function(sound) {
            var src = "";
            if (sound === "error") {
                src = "/point_of_sale/static/src/sounds/error.wav";
            } else if (sound === "bell") {
                src = "/point_of_sale/static/src/sounds/bell.wav";
            } else {
                console.error("Unknown sound: ", sound);
                return;
            }
            $("body").append('<audio src="' + src + '" autoplay="true"></audio>');
        },

        destroy: function() {
            clearTimeout(this.return_to_main_menu);
            this._super.apply(this, arguments);
        },

        convertMinsToText: function(minutes) {
            var h = Math.floor(minutes / 60);
            var s = Math.floor((minutes - Math.floor(minutes)) * 60);
            var m = Math.floor(minutes) % 60;
            h = h < 10 ? "0" + h : h;
            m = m < 10 ? "0" + m : m;
            s = s < 10 ? "0" + s : s;
            return h + ":" + m + ":" + s;
        },
    });

    core.action_registry.add("mrp_work_barcode_mode", MrpBarcodeMode);

    return MrpBarcodeMode;
});
