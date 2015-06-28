openerp.deltatech_web = function (instance) {
	var _t = instance.web._t;
	var QWeb = instance.web.qweb;
	
	
	/* Extend the Sidebar to add Show Metadata link in the 'More' menu */
	instance.web.Sidebar = instance.web.Sidebar.extend({


		
		
        start: function() {
            var self = this;
            this._super(this);
            
            self.add_items('other', [
                    {   label: _t('Metadata'),
                        callback: self.on_click_metadata,
                        classname: 'oe_share' },

                ]);
          
        },
        
        on_click_metadata: function(item) {
            var view = this.getParent()

            var action = view.getParent().action;
            var context = action.context;
	        if (action.target === 'current'){
	            var active_context = {
	                active_model: action.res_model,
	            };
	            context = new instance.web.CompoundContext(context, active_context).eval();
	            delete context['active_id'];
	            delete context['active_ids'];
	            if (action.res_id){
	                context['active_id'] = action.res_id;
	                context['active_ids'] = [action.res_id];
	            }
	        }
	        var dataset = new instance.web.DataSetSearch(this, action.res_model, context, action.domain);
	        if (action.res_id) {
	            dataset.ids.push(action.res_id);
	            dataset.index = 0;
	        }
	        this.dataset = dataset; 
	        var self = this,
            	current_view = view; //this.views[this.active_view].controller;

            var ids = current_view.get_selected_ids();
            if (ids.length === 1) {
                this.dataset.call('get_metadata', [ids]).done(function(result) {
                    var dialog = new instance.web.Dialog(this, {
                        title: _.str.sprintf(_t("Metadata (%s)"), self.dataset.model),
                        size: 'medium',
                    }, QWeb.render('ViewManagerDebugViewLog', {
                        perm : result[0],
                        format : instance.web.format_value
                    })).open();
                });
            }
            
            
        },
        
    });
}