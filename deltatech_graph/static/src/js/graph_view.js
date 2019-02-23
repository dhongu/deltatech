odoo.define('deltatech_graph.GraphView', function (require) {

var GraphView = require('web.GraphView');


GraphView.include({

    init: function (viewInfo) {
        this._super.apply(this, arguments);
        //this.loadParams.discrete = viewInfo.arch.attrs.discrete ? JSON.parse(viewInfo.arch.attrs.discrete) : false;
        this.rendererParams.discrete = viewInfo.arch.attrs.stacked == "discrete";
        var groupBys = [];
        var measure;
        var color;
        viewInfo.arch.children.forEach(function (field) {
            var name = field.attrs.name;

            if (field.attrs.type === 'measure') {
                measure = name;
            }  else {
                groupBys.push(name);
                if (field.attrs.type === 'color') {
                    color = name;
                };
            }

        });
        this.loadParams.groupBys = groupBys || [];
        this.loadParams.color = color;
    }
});



});