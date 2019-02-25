odoo.define('deltatech_graph.GraphController', function (require) {

var GraphController = require('web.GraphController');


GraphController.include({


    custom_events: _.extend({}, GraphController.prototype.custom_events, {
        bar_click: '_onBarClick',
    }),


    init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
        this.views = parent.action.views;
        this.title = parent.action.name;
    },

    _onBarClick: function (event) {
        console.log(event);

        var state = this.model.get();
        var domain = event.data.domain;
        var views = [[false,'list'],[false,'form']]
        //var colDomain = this.model.getHeader($target.data('col_id')).domain;
        //var rowDomain = this.model.getHeader($target.data('id')).domain;
        var context = _.omit(state.context, function (val, key) {
           return key === 'group_by' || _.str.startsWith(key, 'search_default_');
        });

        this.do_action({
            type: 'ir.actions.act_window',
            name: this.title,
            res_model: this.modelName,
            views: views,
            view_type: 'list',
            view_mode: 'list',
            target: 'current',
            context: context,
            domain: event.data.data.domain,  //state.domain.concat(domain),
        });

    }


});



});
