odoo.define('deltatech_mrp_confirmation.mrp_barcode_mode', function (require) {
"use strict";

var core = require('web.core');
//var Model = require('web.Model');
var Widget = require('web.Widget');
var Session = require('web.session');
//var BarcodeHandlerMixin = require('barcodes.BarcodeHandlerMixin');

var QWeb = core.qweb;
var _t = core._t;


var MrpBarcodeMode = Widget.extend({

    events: {
        "click .o_mrp_confirmation_barcode_button_search": function() {
            var modal = $('#barcodeModal');
            this.barcode = modal.find('.modal-body input').val();
            modal.modal('hide');
            return this.on_barcode_scanned(this.barcode);
        },

        "click .o_mrp_confirmation_barcode_button_save":function() {
            this.on_barcode_scanned('#save');
        },

        "click .o_mrp_confirmation_barcode_button_close":function() {
            clearTimeout(self.return_to_main_menu);
            this.do_action('deltatech_mrp_confirmation.mrp_confirmation_action_barcode_mode', {clear_breadcrumbs: true});
        },

        'change .quantity':function(oEvent) {
            var qty_producing = parseFloat($('.quantity')[0].value)
            if (( qty_producing + this.conf.qty_produced ) > this.conf.qty_ready_prod ) {
                qty_producing = this.conf.qty_ready_prod - this.conf.qty_produced
                $('.quantity')[0].value = qty_producing
            }
        },

    },


    start: function () {
        var self = this;
        this.barcode = '';
        var def = this._rpc({
                model: 'mrp.production.conf',
                method: 'create',
                args: [{}],
            })
            .then(function (id){
                self.conf_wizard_id = id;
            });


        core.bus.on('barcode_scanned', this, this._onBarcodeScanned);
        self.session = Session;
        var def = this._rpc({
                model: 'res.company',
                method: 'search_read',
                args: [[['id', '=', this.session.company_id]], ['name']],
            })
            .then(function (companies){
                self.company_name = companies[0].name;
                self.company_image_url = self.session.url('/web/image', {model: 'res.company', id: self.session.company_id, field: 'logo',});
                self.$el.html(QWeb.render("MrpConfirmationBarcodeMode", {widget: self}));
            });
        return $.when(def, this._super.apply(this, arguments));
    },




    display_data: function(){
        var self = this;
        self.session = Session;
        this._rpc({
                model: 'mrp.production.conf',
                method: 'search_read',
                args: [ [['id', '=', self.conf_wizard_id]]  ],
            })
            .then(function (conf){
                self.conf = conf[0];
                if (self.conf.procurement_group_id) {
                    self.display_info(self.conf)
                }
                self.$(".o_mrp_confirmation_barcode_item").html(QWeb.render("MrpConfirmationBarcodeItem", {conf: conf[0]}));
            });

        var time_out = 25000;
        if (Session.debug) {
            time_out = 500000;
        }

        this.return_to_main_menu = setTimeout( function() { self.on_barcode_scanned('#save'); }, time_out);

    },

    display_info: function(conf){
        var self = this;


        var filter = [['procurement_group_id', '=', conf.procurement_group_id[0]]]
        if (self.conf.code) {
            filter = [['code', '=', self.conf.code],
                      ['procurement_group_id', '=', conf.procurement_group_id[0]]]
        }
        this._rpc({
                model: 'mrp.workorder',
                method: 'search_read',
                args: [  filter , ['product_id','qty_produced','qty_production']],
            }).then(function (workorder_data){
               self.$(".o_mrp_confirmation_barcode_mode_info").html(QWeb.render("MrpConfirmationBarcodeModeInfo", {workorder: workorder_data}));
        });
    },

    _onBarcodeScanned: function(barcode) {
            this.on_barcode_scanned(barcode)
      },

    on_barcode_scanned: function(barcode, display ) {
        if (display === undefined) {
            display = true;
        }
        var self = this;
        if (this.return_to_main_menu) {  // in case of multiple scans in the greeting message view, delete the timer, a new one will be created.
            clearTimeout(this.return_to_main_menu);
        }

        this._rpc({
                model: 'mrp.production.conf',
                method: 'search_scanned',
                args: [  self.conf_wizard_id, barcode  ],
            })
            .then(function(result) {
                if (result.action) {
                    self.do_action(result.action);
                } else if (result.warning) {
                    self.do_warn(_('Warning'),result.warning.message);
                }

                if (display) {
                    self.display_data();
                }
                if (barcode=="#save"){
                    clearTimeout(self.return_to_main_menu);
                    self.do_action('deltatech_mrp_confirmation.mrp_confirmation_action_barcode_mode', {clear_breadcrumbs: true});

                }
            });

    },

    destroy: function () {
        clearTimeout(this.return_to_main_menu);
        this._super.apply(this, arguments);
    },
});

core.action_registry.add('mrp_confirmation_barcode_mode', MrpBarcodeMode);

return MrpBarcodeMode;

});
