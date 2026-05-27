/** @odoo-module **/

import options from "@web_editor/js/editor/snippets.options";

export const StatsCountersOptions = options.Class.extend({
    /**
     * @override
     */
    onBuilt: function () {
        this._super(...arguments);
        this.updateCounters();
    },

    /**
     * @override
     */
    onTargetShow: function () {
        this._super(...arguments);
        this.updateCounters();
    },

    /**
     * @see {options.Class}
     */
    target: function (previewMode, widgetValue, params) {
        this.updateCounters();
    },

    /**
     * @see {options.Class}
     */
    format: function (previewMode, widgetValue, params) {
        this.updateCounters();
    },

    /**
     * @override
     */
    cleanForSave: async function () {
        await this._super(...arguments);
        // Ensure counters are at their final state before saving
        this.updateCounters();
    },

    updateCounters: function () {
        if (!this.owner) {
            return;
        }
        const publicWidgets = this.owner.getPublicWidgets(this.$target.closest(".s_deltatech_stats_counters")[0]);
        if (publicWidgets) {
            publicWidgets.forEach((widget) => {
                if (widget.setCountersToTarget) {
                    widget.setCountersToTarget();
                }
            });
        }
    },
});

options.registry.StatsCountersOptions = StatsCountersOptions;

export default {
    StatsCountersOptions,
};
