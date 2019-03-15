odoo.define('deltatech_download.ActionManager', function (require) {
"use strict";

var ActionManager = require('web.ActionManager');
var session = require('web.session');
var framework = require('web.framework');


var wkhtmltopdf_state;


/**
 * This helper will generate an object containing the report's url (as value)
 * for every qweb-type we support (as key). It's convenient because we may want
 * to use another report's type at some point (for example, when `qweb-pdf` is
 * not available).
 */
var make_report_url = function (action) {
    var report_urls = {
        'qweb-html': '/report/html/' + action.report_name,
        'qweb-pdf': '/report/pdf/' + action.report_name,
    };
    // We may have to build a query string with `action.data`. It's the place
    // were report's using a wizard to customize the output traditionally put
    // their options.
    if (_.isUndefined(action.data) || _.isNull(action.data) || (_.isObject(action.data) && _.isEmpty(action.data))) {
        if (action.context.active_ids) {
            var active_ids_path = '/' + action.context.active_ids.join(',');
            // Update the report's type - report's url mapping.
            report_urls = _.mapObject(report_urls, function (value, key) {
                return value += active_ids_path;
            });
        }
    } else {
        var serialized_options_path = '?options=' + encodeURIComponent(JSON.stringify(action.data));
        serialized_options_path += '&context=' + encodeURIComponent(JSON.stringify(action.context));
        // Update the report's type - report's url mapping.
        report_urls = _.mapObject(report_urls, function (value, key) {
            return value += serialized_options_path;
        });
    }
    return report_urls;
};


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

    ir_actions_report: function (action, options) {

        if (action.report_type != 'qweb-pdf') {
            this._super.apply(this, arguments);
        }
         else {
            var self = this;
            action = _.clone(action);
            var report_urls = make_report_url(action);
            var url = '/report/pdf/' + action.report_name;
            framework.blockUI();
            (wkhtmltopdf_state = wkhtmltopdf_state || this._rpc({route: '/report/check_wkhtmltopdf'})).then(function (state) {
                // Display a notification to the user according to wkhtmltopdf's state.

                if (state === 'upgrade' || state === 'ok') {
                    // Trigger the download of the PDF report.
                    var response;


                    var treated_actions = [];
                    var current_action = action;
                    do {
                        report_urls = make_report_url(current_action);
                        var myWindow = window.open(report_urls['qweb-pdf'], '_blank');
                        treated_actions.push(current_action);
                        current_action = current_action.next_report_to_generate;
                    } while (current_action && !_.contains(treated_actions, current_action));
                    //Second part of the condition for security reasons (avoids infinite loop possibilty).
                    framework.unblockUI();
                    self.dialog_stop();
                    return;
                }
            });
        }



     },



})
});