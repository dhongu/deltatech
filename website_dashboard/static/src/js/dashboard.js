odoo.define('website_dashboard.dashboard', function (require) {
"use strict";

var core = require('web.core');
var Model = require('web.Model');
var Widget = require('web.Widget');
var session = require('web.session');

var QWeb = core.qweb;
var _t = core._t;

var Dashboard =  Widget.extend({


    events: {

        'click .tile-card': 'handle_click',
    },


    }
});

core.action_registry.add('mrp_confirmation_barcode_mode', MrpBarcodeMode);

return Dashboard;

});
