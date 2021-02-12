openerp.deltatech_mail = function (instance) {
	var _t = instance.web._t;
	var QWeb = instance.web.qweb;

    function has_follower(self, res_model, yes, no) {
        if (!self.follower_flag) {
        	self.follower_flag = $.Deferred(function() {
                var func = new instance.web.Model("mail.send.to").get_func("has_follower");
                func( res_model).then(function(res) {
                    if(res) {
                    	self.follower_flag.resolve();
                    } else {
                    	self.follower_flag.reject();
                    }
                });
            });
        }
        self.follower_flag.done(yes).fail(no);
    }	
	
    function launch_wizard(self, view){
        var action = view.getParent().action;
        var context = action.context;  
        var MailSendTo = new instance.web.DataSet(self, 'mail.send.to', view.dataset.get_context());
               
        var domain = new instance.web.CompoundDomain(view.dataset.domain);
        if (view.fields_view.type == 'form') {
            domain = new instance.web.CompoundDomain(domain, [['id', '=', view.datarecord.id]]);
        }
        if (view.fields_view.type == 'form') rec_name = view.datarecord.name;
        else rec_name = '';
        instance.web.pyeval.eval_domains_and_contexts({
            domains: [domain],
            contexts: [MailSendTo.get_context()]
        }).done(function (result) {
        	MailSendTo.create({
        		subject:'',
                domain: result.domain,
                action_id: action.id
            }).done(function(mailsend_id) {
            	var selected_ids = view.get_selected_ids();
            	var context = MailSendTo.get_context();
            	context['active_ids'] = selected_ids
                var step1 = MailSendTo.call('go_step_1', [[mailsend_id], selected_ids, context]).done(function(result) {
                    var action = result;
                    self.do_action(action);
                });
            });
        });      	
    }	

    function make_as_read(self, view){
        var action = view.getParent().action;
        var context = action.context; 
        var selected_ids = view.get_selected_ids();
      
        var records = new instance.web.DataSetSearch(self, action.res_model);
         
        records.call('message_mark_as_read',[selected_ids] ).then(
        		
        		function (results) {
        		try{ 
        			view.reload_content();
        		}catch(e){}	
        });
        

    }

    function make_as_unread(self, view){
        var action = view.getParent().action;
        var context = action.context; 
        var selected_ids = view.get_selected_ids();
        
        
        var records = new instance.web.DataSetSearch(self, action.res_model);
        records.call('message_mark_as_unread',[selected_ids] ).then(
        		
        		function (results) {
        		try {
        			view.reload_content();
        		}catch(e){}
        });
        

    }    

    
    
	/* Extend the Sidebar to add Send Mail link in the 'More' menu */
//	instance.web.Sidebar = instance.web.Sidebar.extend({
//
//          start: function() {
//            var self = this;
//            this._super(this);
//            var view = this.getParent()
//            var action = view.getParent().action;
//            has_follower(this, action.res_model, function() {
//                self.add_items('other', [
//                                    //     {   label: _t('Send Mail'),
//                                    //         callback: self.on_click_mail_send },
//                                         {   label: _t('Make Read'),
//                                             callback: self.on_click_make_read },
//                                         {   label: _t('Make UnRead'),
//                                             callback: self.on_click_make_unread },
//                                         ]);
//            });
//
//
//        },
//        on_click_mail_send: function(item) {
//            var view = this.getParent()
//            	launch_wizard(this, view);
//        },
//
//        on_click_make_read: function(item) {
//            var view = this.getParent()
//        	make_as_read(this, view);
//        },
//
//        on_click_make_unread: function(item) {
//            var view = this.getParent()
//        	make_as_unread(this, view);
//        },
//
//
//    });
}