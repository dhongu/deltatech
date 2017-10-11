odoo.define('deltatech.Sidebar', function (require) {

var core = require('web.core');
var data = require('web.data');
var formats = require('web.formats');
var Widget = require('web.Widget');
var Sidebar = require('web.Sidebar');
var Dialog = require('web.Dialog');
var QWeb = core.qweb;
var _t = core._t;



/* Extend the Sidebar to add Show Metadata link in the 'More' menu */
Sidebar.include({

        start: function() {
            var self = this;
            this._super(this);
            
            self.add_items('other', [
                    {   label: _t('Metadata'),
                        callback: self.get_metadata,
                        classname: 'oe_share' },
                ]);
          
        },
        
        get_metadata: function() {
            var view = this.getParent();

            var action = view.getParent().action;
            var context = action.context;
	        if (action.target === 'current'){
	            var active_context = {
	                active_model: action.res_model,
	            };
	            context = new data.CompoundContext(context, active_context).eval();
	            delete context['active_id'];
	            delete context['active_ids'];
	            if (action.res_id){
	                context['active_id'] = action.res_id;
	                context['active_ids'] = [action.res_id];
	            }
	        }
	        var dataset = new data.DataSetSearch(this, action.res_model, context, action.domain);
	        if (action.res_id) {
	            dataset.ids.push(action.res_id);
	            dataset.index = 0;
	        }
	        this.dataset = dataset;
	        var self = this,
            	current_view = view; //this.views[this.active_view].controller;

            var ids = current_view.get_selected_ids();
            var ds = dataset;
            /*
            var ds = this._view_manager.dataset;
            if (!this._active_view.controller.get_selected_ids().length) {
                console.warn(_t("No metadata available"));
                return
            }
            */
            ds.call('get_metadata', [ids]).done(function(result) {
                new Dialog(this, {
                    title: _.str.sprintf(_t("Metadata (%s)"), ds.model),
                    size: 'medium',
                    $content: QWeb.render('WebClient.DebugViewLog', {
                        perm : result[0],
                        format : formats.format_value
                    })
                }).open();
            });
        },
        
    });




});


