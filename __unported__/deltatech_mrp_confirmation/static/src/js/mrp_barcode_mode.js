odoo.define('deltatech_mrp_confirmation.mrp_barcode_mode', function (require) {
"use strict";

var core = require('web.core');
var Model = require('web.Model');
var Widget = require('web.Widget');
var session = require('web.session');
var BarcodeHandlerMixin = require('barcodes.BarcodeHandlerMixin');

var QWeb = core.qweb;
var _t = core._t;


var MrpBarcodeMode = Widget.extend(BarcodeHandlerMixin, {

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

    init: function (parent, action) {
        // Note: BarcodeHandlerMixin.init calls this._super.init, so there's no need to do it here.
        // Yet, "_super" must be present in a function for the class mechanism to replace it with the actual parent method.
        this._super;
        var self = this;
        this.barcode = '';
        this.conf_wizard = new Model('mrp.production.conf');
        this.conf_wizard.call("create",[{}]).then(function(id) {
            self.conf_wizard_id = id;
        });

        BarcodeHandlerMixin.init.apply(this, arguments);
    },

    start: function () {
        var self = this;
        self.session = session;
        var res_company = new Model('res.company');
        res_company.query(['name'])
           .filter([['id', '=', self.session.company_id]])
           .all()
           .then(function (companies){
                self.company_name = companies[0].name;
                self.company_image_url = self.session.url('/web/image', {model: 'res.company', id: self.session.company_id, field: 'logo',})
                self.$el.html(QWeb.render("MrpConfirmationBarcodeMode", {widget: self}));

            });
        return self._super.apply(this, arguments);
    },

    display_data: function(){
        var self = this;
        self.session = session;
        //var conf_wizard = new Model('mrp.production.conf');

        self.conf_wizard.query()  //['production_id','worker_id','operation_id','code']
            .filter([['id', '=', self.conf_wizard_id]])
           .all()
           .then(function (conf){
                self.conf = conf[0];
                if (self.conf.procurement_group_id) {
                    self.display_info(self.conf)
                }
                self.$(".o_mrp_confirmation_barcode_item").html(QWeb.render("MrpConfirmationBarcodeItem", {conf: conf[0]}));
           });


        var time_out = 25000;
        if (session.debug) {
            time_out = 500000;
        }

        this.return_to_main_menu = setTimeout( function() { self.on_barcode_scanned('#save'); }, time_out);

    },

    display_info: function(conf){
        var self = this;
        var workorder = new Model('mrp.workorder');

        var filter = [['procurement_group_id', '=', conf.procurement_group_id[0]]]
        if (self.conf.code) {
            filter = [['code', '=', self.conf.code],
                      ['procurement_group_id', '=', conf.procurement_group_id[0]]]
        }
        workorder.query(['product_id','qty_produced','qty_production'])

               .filter(filter)
               .all()
               .then(function (workorder_data){
               self.$(".o_mrp_confirmation_barcode_mode_info").html(QWeb.render("MrpConfirmationBarcodeModeInfo", {workorder: workorder_data}));
        });
    },


    on_barcode_scanned: function(barcode, display ) {
        if (display === undefined) {
            display = true;
        }
        var self = this;
        if (this.return_to_main_menu) {  // in case of multiple scans in the greeting message view, delete the timer, a new one will be created.
            clearTimeout(this.return_to_main_menu);
        }
        self.conf_wizard.call("search_scanned",  [self.conf_wizard_id, barcode] )
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
