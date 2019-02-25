odoo.define('deltatech_graph.GraphModel', function (require) {

var GraphModel = require('web.GraphModel');


GraphModel.include({


    load: function (params) {
        if ('color' in params) {
            this.color = params.color;
        } else {
            this.color = false;
        }

        return this._super.apply(this, arguments);
    },

    reload: function (handle, params) {
        if ('color' in params) {
            this.chart.color = params.color;
        }
        return this._super.apply(this, arguments);

    },

    _processData: function (raw_data) {
         this._super.apply(this, arguments);

         for (var i = 0; i < raw_data.length; i++) {
            data_pt = raw_data[i];
            line = this.chart.data[i];
            if (this.color) {
                line.color = data_pt[this.color];
            }
            line.domain = data_pt.__domain;
         }
    }

});



});