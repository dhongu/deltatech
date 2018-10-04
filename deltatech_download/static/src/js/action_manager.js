odoo.define('deltatech_pos.ActionManager', function (require) {
"use strict";

var ActionManager = require('web.ActionManager');
var session = require('web.session');
var framework = require('web.framework');

ActionManager.include({
    ir_actions_act_url: function (action, options) {
        var url = action.url;
        if (session.debug && url && url.length && url[0] === '/') {
            url = $.param.querystring(url, {debug: session.debug});
        }
        this.dialog_stop();
        if (action.target === 'self') {
            framework.redirect(url);
            return $.Deferred(); // The action is finished only when the redirection is done
        } else {
            window.open(url, '_blank');
            options.on_close();
        }
        return $.when();
    },

})
});