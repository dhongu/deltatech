odoo.define('web_map.MapController', function (require) {
    'use strict';
    var AbstractController = require('web.AbstractController');
    var core = require('web.core');
    var qweb = core.qweb;
    var Pager = require('web.Pager');
    var MapController = AbstractController.extend({

        custom_events: _.extend({}, AbstractController.prototype.custom_events, {
            'pin_clicked': '_onPinClick',
            'get_itinerary_clicked': '_onGetItineraryClicked',
            'open_clicked': '_onOpenClicked',
        }),

        //---------------------------------------------------------------------------------
        //Public
        //-----------------------------------------------------------------------------

        /**
         * @override
         * @param {JqueryElement} $node
         */

        renderButtons: function ($node) {
            var url = 'https://www.google.com/maps/dir/?api=1';
            if (this.model.data.records.length) {
                url += '&waypoints=';
                var all_coord = this.model.data.records.filter((record) => record.partner && record.partner.partner_latitude && record.partner.partner_longitude);
                _.uniq(all_coord, function(record){ return record.partner.partner_latitude + '_' + record.partner.partner_longitude; })
                    .forEach((record) => {
                        url += record.partner.partner_latitude + ',' + record.partner.partner_longitude + '|';
                    });
                url = url.slice(0, -1);
            }
            var $buttons = $(qweb.render("MapView.buttons"), { widget: this });
            $buttons.find('a').attr('href', url);
            $buttons.appendTo($node);
        },

        /**
         * @override
         * @param {JqueryElement} $node
         */
        renderPager: function ($node) {
            const params = this._getPagerParams();
            this.pager = new Pager(this, params.size, params.current_min, params.limit);
            this.pager.on('pager_changed', this, newState => {
                this.pager.disable();
                this.reload({ limit: newState.limit, offset: newState.current_min - 1 })
                    .then(this.pager.enable.bind(this.pager));
            });
            return this.pager.appendTo($node);
        },
        /**
         * @override
         */
        update: function () {
            return this._super.apply(this, arguments).then(() => {
                this._updatePager();
            });
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * Return the params (current_min, limit and size) to pass to the pager,
         * according to the current state.
         *
         * @private
         * @returns {Object}
         */
        _getPagerParams: function () {
            const state = this.model.get();
            return {
                current_min: state.offset + 1,
                limit: state.limit,
                size: state.count,
            };
        },
        /**
         * Update the pager with the current state.
         *
         * @private
         */
        _updatePager: function () {
            if (this.pager) {
                this.pager.updateState(this._getPagerParams());
            }
        },

        //-------------------------------------------------------------------------------------
        //Handler
        //------------------------------------------------------------------------------------

        /**
         *
         * @param {MouseEvent} ev
         * @private
         * redirects to google maps with all the records' coordinates
         */
        _onGetItineraryClicked: function (ev) {
            window.open('https://www.google.com/maps/dir/?api=1&destination=' + ev.data.lat + ',' + ev.data.lon);
        },

        /**
         *
         * @param {MouseEvent} ev
         * @private
         * Redirects to a form view in edit mode
         */
        _onOpenClicked: function (ev) {
            this.trigger_up('switch_view', {
                view_type: 'form',
                res_id: ev.data.id,
                mode: 'readonly',
                model: this.modelName
            });
        }
    });
    return MapController;
});
