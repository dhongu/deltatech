odoo.define('deltatech_hr_attendance.attendance_summary_widget', function
(require) {
'use strict';

var Widget = require('web.Widget');

var AttendanceSummaryWidget = Widget.extend({
    events: {
        'click .o_attendance_summary_backend_web_action': 'boundLink',
        'click .o_attendance_summary_backend_web_action_multi': 'boundLinkmulti',
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
        var context = $(e.target).data('context');
        return this.do_action({
            type: 'ir.actions.act_window',
            res_model: res_model,
            res_id: res_id,
            views: [[false, 'form']],
            target: 'current',
            context: context
        });
    },
    boundLinkmulti: function(e) {
        var res_model = $(e.target).data('res-model');
        var res_id = $(e.target).data('active-id');
        return this.do_action({
            type: 'ir.actions.act_window',
            res_model: res_model,
            domain: [["id", "in", res_id]],
            views: [[false, "list"], [false, "form"]],
            target: 'current'
        });
    },
});

return AttendanceSummaryWidget;

});
