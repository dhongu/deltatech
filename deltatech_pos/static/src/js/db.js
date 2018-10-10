odoo.define('deltatech_pos.DB', function (require) {
"use strict";

var PosDB = require('point_of_sale.DB');

PosDB.include({
    _partner_search_string: function(partner){

        var str = this._super(partner);
        str = str.replace('\n','')
        if(partner.vat){
            str += '|' + partner.vat;
        }
        return str+'\n'
    },

})
});