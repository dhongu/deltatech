(function() {
    openerp.web.WebClient.include({
    	
    	// to do: move this to mail.utils
    	send_native_notification: function(title, content) {
    		
            window.Notification.requestPermission();
                		
    	    var notification = new Notification(title, {body: content, icon: "/web_notification/static/src/img/odoo_o.png"});
       
    	    notification.onclick = function (e) {
    	        window.focus();
    	        if (this.cancel) {
    	            this.cancel();
    	        } else if (this.close) {
    	            this.close();
    	        }
    	    };
    	},
    	
    	
        declare_bus_channel: function() {
            this._super();
            var self = this,
                channel = 'notify_res_user_' + this.session.uid;
            this.bus_on(channel, function(message) {
                if (message.mode == 'warn'){
                    var audio = new Audio("/web_notification/static/sound/sounds-w.mp3");
                    
                    audio.play();
                    self.send_native_notification(message.subject, message.body);
                    self.do_warn(message.subject,
                                 message.body,
                                 message.sticky);
                }else{
                    if (message.mode == 'notify'){
                    	 
                        var audio = new Audio("/web_notification/static/sound/sounds-n.mp3");
                        
                        audio.play();
                        self.send_native_notification(message.subject, message.body);
                        self.do_notify(message.subject,
                                       message.body,
                                       message.sticky);
                    }
                }
            });
            this.add_bus_channel(channel);
        },
    });
})();
