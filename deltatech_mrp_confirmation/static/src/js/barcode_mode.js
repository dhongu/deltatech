odoo.define('deltatech_mrp_confirmation.barcode_mode', function (require) {
"use strict";

var core = require('web.core');
var Model = require('web.Model');
var Widget = require('web.Widget');
var Session = require('web.session');
var BarcodeHandlerMixin = require('barcodes.BarcodeHandlerMixin');

var QWeb = core.qweb;
var _t = core._t;


var ConfirmationBarcodeMode = Widget.extend(BarcodeHandlerMixin, {

    init: function (parent, action) {
        // Note: BarcodeHandlerMixin.init calls this._super.init, so there's no need to do it here.
        // Yet, "_super" must be present in a function for the class mechanism to replace it with the actual parent method.
        this._super;
        BarcodeHandlerMixin.init.apply(this, arguments);
    },

    start: function () {
        var self = this;
        self.session = Session;
        var res_company = new Model('res.company');
        res_company.query(['name'])
           .filter([['id', '=', self.session.company_id]])
           .all()
           .then(function (companies){
                self.company_name = companies[0].name;
                self.company_image_url = self.session.url('/web/image', {model: 'res.company', id: self.session.company_id, field: 'logo',})
                self.$el.html(QWeb.render("ConfirmationBarcodeMode", {widget: self}));

            });
        return self._super.apply(this, arguments);
    },

    on_barcode_scanned: function(barcode) {
        var self = this;
        var mrp_confirmation = new Model('mrp.production.conf');
        mrp_confirmation.call('barcode_scan', [barcode, ])
            .then(function (result) {
                if (result.action) {
                    self.do_action(result.action);
                } else if (result.warning) {
                    self.do_warn(result.warning);
                }
            });
    },


    destroy: function () {
        clearInterval(this.clock_start);
        this._super.apply(this, arguments);
    },
});

core.action_registry.add('mrp_confirmation_barcode_mode', ConfirmationBarcodeMode);

return ConfirmationBarcodeMode;

});
