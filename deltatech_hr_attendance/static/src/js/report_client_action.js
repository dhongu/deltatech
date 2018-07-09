odoo.define('deltatech_hr_attendance.client_action', function
(require) {
'use strict';


var Widget = require('web.Widget');
var Report = require('report.client_action');

var ReportAction = Widget.extend(Report, {
    events: {
        'click .o_attendance_summary_backend_web_action': 'boundLink',
    },
    init: function(parent, options) {
        this._super.apply(this, arguments);
        this.options = _.extend(options || {}, {
            csrf_token: odoo.csrf_token,
        });
    },
    start: function() {
        return this._super.apply(this, arguments);
    },
    boundLink: function(e) {
        var res_model = $(e.target).data('res-model');
        var res_id = $(e.target).data('active-id');
        return this.do_action({
            type: 'ir.actions.act_window',
            res_model: res_model,
            res_id: res_id,
            views: [[false, 'form']],
            target: 'current'
        });
    },
});

return   ReportAction;;

});
