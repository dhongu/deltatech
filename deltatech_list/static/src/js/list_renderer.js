odoo.define('deltatech_list.ListRenderer', function (require) {

var ListRenderer = require('web.ListRenderer');
var config = require('web.config');
var field_utils = require('web.field_utils');




ListRenderer.include({

    init: function (parent, state, params) {
        this._super.apply(this, arguments);
        this.selectionIds = params.SelectedIds || [];
    },

    updateState: function (state, params) {
        if (params.SelectedIds) {
            this.selectionIds = params.SelectedIds;
        }
        return this._super.apply(this, arguments);
    },

    _renderRow: function (record) {
        var $tr = this._super.apply(this, arguments);
        $tr.data('res_id', record.res_id)
        return $tr;
    },

    _renderView: function () {
        var self = this;

        var res = this._super();

//        var $info = $('#InfoBody')
//
//        var $legend = $($.parseHTML(this.noContentHelp)).filter('#legend');
//        if ($legend && $info) {
//            $('#InfoBody').empty();
//            $('#InfoBody').append($legend.html());
//        }
//



        if (this.selectionIds.length) {
            var $checked_rows = this.$('tr').filter(function (index, el) {
                var res =  _.contains(self.selectionIds, $(el).data('res_id'));
                if (res) {
                    $(el).find('.o_list_record_selector input').prop('checked', true);
                    self.selection.push($(el).data('id'));
                }
                return res;
            });
            $checked_rows.find('.o_list_record_selector input').prop('checked', true);
        }
        return res;
    },


});



});