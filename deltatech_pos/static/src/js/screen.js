odoo.define('deltatech_pos.screens', function (require) {
"use strict";

var gui = require('point_of_sale.gui');
var screens = require('point_of_sale.screens');
var core = require('web.core');
var QWeb = core.qweb;
var _t = core._t;


 screens.ReceiptScreenWidget.include({
    render_receipt: function() {
        this.prepare_bf()
        this._super();
    },


    prepare_bf: function(){
        var order = this.pos.get_order();
        var textfile = '';
        //        var textfile =  '2;'+ moment().format('L LT') + ' '+ order.name+'\r\n';
        //            textfile = textfile + '2;\r\n';
        //            textfile = textfile + '2;'+  this.pos.company.name +'\r\n';
        var reference = order.name;
        reference = reference.substr(8);
        textfile = textfile + '2;'+reference+'\r\n';
        var orderlines = order.get_orderlines();
        for (var i = 0; i < orderlines.length; i++) {
            var orderline = orderlines[i];
            //verifying length...
            if(orderline.product.display_name.length<=18){
                var prod_name = orderline.product.display_name;
                textfile = textfile +  '1;'+prod_name+';1;1;'+orderline.price*100+';'+orderline.quantity*100000+'\r\n';
            }
            else{
                var prod_name = orderline.product.display_name.substring(0,18);

		var prodname = orderline.product.display_name;
                textfile = textfile +  '1;'+prod_name+';1;1;'+orderline.price*100+';'+orderline.quantity*100000+'\r\n';
                var d_array = prodname.match(/.{1,18}/g);
                for(var j = 1; j < d_array.length; j++){//skip first element
                    textfile = textfile +  '2;' + d_array[j] + '\r\n';
                }
            }


        }
        var paymentlines = order.get_paymentlines();
        for (var i = 0; i < paymentlines.length; i++) {
            var paymentline = paymentlines[i];
            if ( paymentline.cashregister.journal.type == "cash" ){
                if(paymentline.cashregister.journal.code == "VOUC" || paymentline.cashregister.journal.code == "VOUPR"){
                            textfile = textfile + '5;'+paymentline.amount *100+';5;1;0\r\n';
                        }
                else{
                    textfile = textfile + '5;'+paymentline.amount *100+';1;1;0\r\n'
                }
            }
            else{
                textfile = textfile + '5;'+paymentline.amount *100+';3;1;0\r\n'
            }

        }

        var filename = 'ONLINE'+order.name+'.TXT';
        order.file = new Blob([textfile], {type: 'application/octet-stream'});

    },

    download: function(filename, blob) {
        var element = document.createElement('a');
        //element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
        element.setAttribute('href', URL.createObjectURL(blob))
        element.setAttribute('download', filename);

        element.style.display = 'none';
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    },

    print_web: function() {
        var order = this.pos.get_order();
        var filename = 'ONLINE'+order.name+'.TXT';
        this.download(filename, order.file);
        this.pos.get_order()._printed = true;
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
