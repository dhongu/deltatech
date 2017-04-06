function openerp_mrp_widgets(instance){

    var module = instance.deltatech_mrp_confirmation;
    var _t     = instance.web._t;
    var QWeb   = instance.web.qweb;

    // This widget makes sure that the scaling is disabled on mobile devices.
    // Widgets that want to display fullscreen on mobile phone need to extend this
    // widget.

    module.MobileWidget = instance.web.Widget.extend({
        start: function(){
            if(!$('#oe-mobilewidget-viewport').length){
                $('head').append('<meta id="oe-mobilewidget-viewport" name="viewport" content="initial-scale=1.0; maximum-scale=1.0; user-scalable=0;">');
            }
            return this._super();
        },
        destroy: function(){
            $('#oe-mobilewidget-viewport').remove();
            return this._super();
        },
    });

    module.ProductionMenuWidget = module.MobileWidget.extend({
    	
    });
 
    openerp.web.client_actions.add('mrp.menu', 'instance.deltatech_mrp_confirmation.ProductionMenuWidget');

    module.ProductionMainWidget = module.MobileWidget.extend({
        template: 'ProductionMainWidget',
        init: function(parent,params){
            this._super(parent,params);
            var self = this;
            $(window).bind('hashchange', function(){
                var states = $.bbq.getState();
                if (states.action === "mrp.menu"){
                    self.do_action({
                        type:   'ir.actions.client',
                        tag:    'mrp.menu',
                        target: 'current',
                    },{
                        clear_breadcrumbs: true,
                    });
                }
            });
            init_hash = $.bbq.getState();
            
            this.production_id = init_hash.production_id ? init_hash.production_id:undefined;
            this.production = null;
            this.productions = []; 
            
            this.selected_operation = { id: null, production_id: null};
 
            this.barcode_scanner = new module.BarcodeScanner();
 

        },
 
        load: function(mrp_production_id){
        
        },
        start: function(){
            this._super();
            var self = this;
            instance.webclient.set_content_full_screen(true);
            this.barcode_scanner.connect(function(ean){
                self.scan(ean);
            });
            
            this.$('.js_production_quit').click(function(){ self.quit(); });
            this.$('.js_production_prev').click(function(){ self.production_prev(); });
            this.$('.js_production_next').click(function(){ self.production_next(); });
            this.$('.js_production_menu').click(function(){ self.menu(); }); 

        },
        on_searchbox: function(query){
            var self = this;
 
        },
        // reloads the data from the provided picking and refresh the ui.
        // (if no picking_id is provided, gets the first picking in the db)
        refresh_ui: function(picking_id){
            var self = this;
  
        },
        get_header: function(){
            if(this.production){
                return this.production.name;
            }else{
                return '';
            }
        },
        menu: function(){
            $.bbq.pushState('#action=mrp.menu');
            $(window).trigger('hashchange');
        },
        scan: function(ean){ //scans a barcode, sends it to the server, then reload the ui
            var self = this;
            var product_visible_ids = this.picking_editor.get_visible_ids();
            return new instance.web.Model('stock.picking')
                .call('process_barcode_from_ui', [self.picking.id, ean, product_visible_ids])
                .then(function(result){
                    if (result.filter_loc !== false){
                        //check if we have receive a location as answer
                        if (result.filter_loc !== undefined){
                            var modal_loc_hidden = self.$('#js_LocationChooseModal').attr('aria-hidden');
                            if (modal_loc_hidden === "false"){
                                var line = self.$('#js_LocationChooseModal .js_loc_option[data-loc-id='+result.filter_loc_id+']').attr('selected','selected');
                            }
                            else{
                                self.$('.oe_searchbox').val(result.filter_loc);
                                self.on_searchbox(result.filter_loc);
                            }
                        }
                    }
                    if (result.operation_id !== false){
                        self.refresh_ui(self.picking.id).then(function(){
                            return self.picking_editor.blink(result.operation_id);
                        });
                    }
                });
        },
  
        drop_down: function(){
            var self = this;
            var pack_op_ids = self.picking_editor.get_current_op_selection(true);
            if (pack_op_ids.length !== 0){
                return new instance.web.Model('stock.pack.operation')
                    .call('action_drop_down', [pack_op_ids])
                    .then(function(){
                            return self.refresh_ui(self.picking.id).then(function(){
                                if (self.picking_editor.check_done()){
                                    return self.done();
                                }
                            });
                    });
            }
        },
 
        quit: function(){
            this.destroy();
            return new instance.web.Model("ir.model.data").get_func("search_read")([['name', '=', 'action_picking_type_form']], ['res_id']).pipe(function(res) {
                    window.location = '/web#action=' + res[0]['res_id'];
                });
        },
        destroy: function(){
            this._super();
            // this.disconnect_numpad();
            this.barcode_scanner.disconnect();
            instance.webclient.set_content_full_screen(false);
        },
    });
    
    openerp.web.client_actions.add('mrp.ui', 'instance.deltatech_mrp_confirmation.ProductionMainWidget');

    module.BarcodeScanner = instance.web.Class.extend({
        connect: function(callback){
            var code = "";
            var timeStamp = 0;
            var timeout = null;

            this.handler = function(e){
                if(e.which === 13){ //ignore returns
                    return;
                }

                if(timeStamp + 50 < new Date().getTime()){
                    code = "";
                }

                timeStamp = new Date().getTime();
                clearTimeout(timeout);

                code += String.fromCharCode(e.which);

                timeout = setTimeout(function(){
                    if(code.length >= 3){
                        callback(code);
                    }
                    code = "";
                },100);
            };

            $('body').on('keypress', this.handler);

        },
        disconnect: function(){
            $('body').off('keypress', this.handler);
        },
    });

}

openerp.deltatech_mrp_confirmation = function(openerp) {
    openerp.deltatech_mrp_confirmation = openerp.deltatech_mrp_confirmation || {};
    openerp_mrp_widgets(openerp);
}
