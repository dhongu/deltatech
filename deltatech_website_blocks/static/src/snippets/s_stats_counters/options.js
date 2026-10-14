/** @odoo-module **/

import options from "@web_editor/js/editor/snippets.options";

options.registry.StatsCountersOptions = options.Class.extend({

    onBuilt() {
        this._super(...arguments);
        this._updateCounters();
    },

    async onTargetShow() {
        await this._super(...arguments);
        this._updateCounters();
    },

    async cleanForSave() {
        await this._super(...arguments);
        this._updateCounters();
    },

    // Called when "Target Value" or "Format" widgets change (data-select-data-attribute).
    async selectDataAttribute(previewMode, widgetValue, params) {
        await this._super(...arguments);
        if (params.attributeName === "target" || params.attributeName === "format") {
            this._updateCounters();
        }
    },

    // Mirrors StatsCounters.setCountersToTarget() from 000.js.
    _updateCounters() {
        const section = this.$target[0].closest(".s_deltatech_stats_counters") || this.$target[0];
        section.querySelectorAll(".count").forEach((el) => {
            const target = Number(el.dataset.target || 0);
            const mode = el.dataset.format || "plain";
            el.textContent = mode === "group"
                ? Math.round(target).toLocaleString("en-US")
                : String(Math.round(target));
        });
    },
});

export default options.registry.StatsCountersOptions;