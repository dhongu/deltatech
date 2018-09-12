odoo.define('deltatech_pos.screens', function (require) {
"use strict";

var gui = require('point_of_sale.gui');
var screens = require('point_of_sale.screens');
var core = require('web.core');
var models = require('point_of_sale.models');
var QWeb = core.qweb;
var _t = core._t;

/*
if (!String.prototype.format) {
  String.prototype.format = function() {
    var args;
    args = arguments;
    if (args.length === 1 && args[0] !== null && typeof args[0] === 'object') {
      args = args[0];
    }
    return this.replace(/{([^}]*)}/g, function(match, key) {
      return (typeof args[key] !== "undefined" ? args[key] : match);
    });
  };
}*/


models.load_fields('account.journal', ['cod_ecr']);


screens.ReceiptScreenWidget.include({
    render_receipt: function() {
        this.prepare_bf();
        this._super();
    },

    get_ecr_setting:function(ecr_type){
        var ecr = {}
        switch(ecr_type) {
        case 'datecs18':
            ecr = {
                p:'P,1,______,_,__;', // comanda print
                s:'S,1,______,_,__;', // comanda sale
                t:'T,1,______,_,__;', // comanda de inchidere
                limit:72,
                c_a:1,
                c_q:1
             }
            break;
        case 'optima':
            ecr = {
                p:'2;', // comanda print
                s:'1;', // comanda sale
                t:'5;', // comanda de inchidere
                limit:18,
                c_a:100,
                c_q:100000
            }
            break;
        }
     return  ecr;
    },

    prepare_bf: function(){
        var order = this.pos.get_order();
        var textfile = '';

        var ecr = this.get_ecr_setting(this.pos.config.ecr_type);


        var reference = order.uid;

        textfile = textfile + ecr.p +reference+'\r\n';
        var orderlines = order.get_orderlines();
        for (var i = 0; i < orderlines.length; i++) {
            var orderline = orderlines[i];
            var product_display_name = orderline.product.display_name;
            product_display_name = product_display_name.replace(/,/g , " ");
            product_display_name = product_display_name.replace(/;/g , " ");

            //verifying length...
            if(product_display_name.length<=ecr.limit){
                var prod_name = product_display_name;
                textfile = textfile +  ecr.s +prod_name+';1;1;'+orderline.price*ecr.c_a+';'+orderline.quantity*ecr.c_q+'\r\n';
            }
            else{
                var prod_name = product_display_name.substring(0,ecr.limit);
		        var prodname = product_display_name;

                textfile = textfile +  ecr.s +prod_name+';1;1;'+orderline.price*ecr.c_a+';'+orderline.quantity*ecr.c_q+'\r\n';
                var d_array = prodname.match(/.{1,ecr.limit}/g);
                for(var j = 1; j < d_array.length; j++){//skip first element
                    textfile = textfile +  ecr.p + d_array[j] + '\r\n';
                }
            }


        }
        var paymentlines = order.get_paymentlines();
        for (var i = 0; i < paymentlines.length; i++) {
            var paymentline = paymentlines[i];
            var cod_ecr = paymentline.cashregister.journal.cod_ecr;
            textfile = textfile + ecr.t +paymentline.amount*ecr.c_a+';'+cod_ecr+';1;0\r\n'
        }


        order.file = new Blob([textfile], {type: 'application/octet-stream'});

    },

    download: function(filename, blob) {
        var element = document.createElement('a');

        element.setAttribute('href', URL.createObjectURL(blob))
        element.setAttribute('download', filename);

        element.style.display = 'none';
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    },

    print_web: function() {
        var order = this.pos.get_order();
        var filename = this.pos.config.file_prefix +order.uid+'.'+this.pos.config.file_ext;
        this.download(filename, order.file);
        this.pos.get_order()._printed = true;
        this.click_next();
    },

    click_next: function(){
        if(this.pos.get_order()._printed){
    		this._super();
    	}
    	else{
    	    this.gui.show_popup('error',{
                    'title': _t('Error: Nu ati tiparit bonul fiscal!'),
                    'body': "Apasati pe botonul de tiparire pentru ca bonul fiscal sa fie tiparit de casa de marcat",
                }
    	    );

    	}

    },

 });


});
