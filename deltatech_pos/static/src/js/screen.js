odoo.define('deltatech_pos.screens', function (require) {
"use strict";

var gui = require('point_of_sale.gui');
var screens = require('point_of_sale.screens');
var core = require('web.core');
var models = require('point_of_sale.models');
var QWeb = core.qweb;
var _t = core._t;


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
}


models.load_fields('account.journal', ['cod_ecr']);


screens.ReceiptScreenWidget.include({
    render_receipt: function() {
        this.prepare_bf();
        this._super();
    },

    get_ecr_setting:function(ecr_type){
        var ecr = {};
        switch(ecr_type) {
        case 'datecs18':
            ecr = {

                print:'P,1,______,_,__;{text};;;;', // comanda print
                sale:'S,1,______,_,__;{name};{price};{qty};{dep};{group};{tax};0;0;{uom};', // comanda sale
                total:'T,1,______,_,__;{type};{amount};;;;', // comanda de inchidere
                discount: 'C,1,______,_,__;{typr};{value};;;;',
                limit:72,
                amount:function(value){return value.toFixed(2);},
                qty:function(value){return value.toFixed(3);}
             };
            break;
        case 'optima':
            ecr = {
                print:'2;{text}',                   // comanda print
                sale:'1;{name};1;1;{price};{qty}',  // comanda sale
                total:'5;{amount};{type};1;0',      // comanda de inchidere
                discount:'',
                limit:18,
                amount:function(value){return value*100;},
                qty:function(value){return value*100000;}

            };
            break;
        }
     return  ecr;
    },

    prepare_bf: function(){
        var order = this.pos.get_order();
        var textfile = '';
        var line = '';
        var ecr = this.get_ecr_setting(this.pos.config.ecr_type);


        var reference = order.uid;
        line = ecr.print.format({'text':reference});
        textfile = textfile +line + '\r\n';
        //textfile = textfile + ecr.p +reference+'\r\n';
        var orderlines = order.get_orderlines();
        for (var i = 0; i < orderlines.length; i++) {
            var orderline = orderlines[i];
            var product_display_name = orderline.product.display_name;
            product_display_name = product_display_name.replace(/,/g , " ");
            product_display_name = product_display_name.replace(/;/g , " ");

            //verifying length...
            if(product_display_name.length<=ecr.limit){
                var prod_name = product_display_name;
            }
            else{
                var prod_name = product_display_name.substring(0,ecr.limit);
		        var prodname = product_display_name;
            }

            line = ecr.sale.format({
                'name':prod_name,
                'price':ecr.amount(orderline.price),
                'qty':ecr.qty(orderline.quantity),
                'dep':'1',
                'group':'1',
                'tax':'1',  // de adus codul de taxa model
                'uom':orderline.product.uom_id[1]
            });
            textfile = textfile +line + '\r\n';


            if(product_display_name.length>ecr.limit){
                var d_array = prodname.match(/.{1,ecr.limit}/g);
                for(var j = 1; j < d_array.length; j++){
                    line = ecr.print.format({'text':d_array[j]});
                    textfile = textfile +line + '\r\n';
                }
            }
            if (orderline.discount>0){
                line = ecr.discount.format({'type':1,'value':ecr.amount(orderline.discount)});
                textfile = textfile +line + '\r\n';
            }

        }
        var paymentlines = order.get_paymentlines();
        for (var i = 0; i < paymentlines.length; i++) {
            var paymentline = paymentlines[i];
            var cod_ecr = paymentline.cashregister.journal.cod_ecr;
            line = ecr.total.format({'type':cod_ecr, 'amount':ecr.amount(paymentline.amount)});
            textfile = textfile +line + '\r\n';
            //textfile = textfile + ecr.t +paymentline.amount*ecr.c_a+';'+cod_ecr+';1;0\r\n';
        }


        order.file = new Blob([textfile], {type: 'application/octet-stream'});

    },

    download: function(filename, blob) {
        var element = document.createElement('a');

        element.setAttribute('href', URL.createObjectURL(blob));
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
                    'body': "Apasati pe botonul de tiparire pentru ca bonul fiscal sa fie tiparit de casa de marcat"
                }
    	    );

    	}

    }

 });


});
