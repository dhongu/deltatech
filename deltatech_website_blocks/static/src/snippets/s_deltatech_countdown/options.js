/** @odoo-module **/

import options from "@web_editor/js/editor/snippets.options";

options.registry.DeltatechCountdownOptions = options.Class.extend({
    /**
     * @override
     */
    onBuilt() {
        this._super.apply(this, arguments);
        const $container = this.$target.find(".s_deltatech_countdown_container");
        // Default to 1 week from now if not set
        if (!$container.attr("data-end-date")) {
            const nextWeek = new Date();
            nextWeek.setDate(nextWeek.getDate() + 7);
            const iso = nextWeek.toISOString();
            $container.attr("data-end-date", iso);
        }
    },

    /**
     * @override
     */
    async onTargetShow() {
        await this._super.apply(this, arguments);
        const $container = this.$target.find(".s_deltatech_countdown_container");
        const endDateIso = $container.attr("data-end-date") || "";
        if (endDateIso) {
            const dateObj = new Date(endDateIso);
            if (!isNaN(dateObj.getTime())) {
                const year = dateObj.getFullYear();
                const month = String(dateObj.getMonth() + 1).padStart(2, "0");
                const day = String(dateObj.getDate()).padStart(2, "0");
                const dateStr = `${year}-${month}-${day}`;
                const timeStr =
                    String(dateObj.getHours()).padStart(2, "0") + ":" + String(dateObj.getMinutes()).padStart(2, "0");
                this.$el.find('[data-name="end_date"]').val(dateStr);
                this.$el.find('[data-name="end_time"]').val(timeStr);
            }
        }
        const confetti = $container.attr("data-confetti");
        this.$el.find('[data-name="confetti_toggle"]').prop("checked", confetti === "true");
    },

    // Handlers for the options menu
    updateEndDate(previewMode, value) {
        const $container = this.$target.find(".s_deltatech_countdown_container");
        let currentIso = $container.attr("data-end-date");
        let date = currentIso ? new Date(currentIso) : new Date();
        if (isNaN(date.getTime())) date = new Date();

        if (value) {
            const [year, month, day] = value.split("-").map(Number);
            date.setFullYear(year, month - 1, day);
        }
        const newIso = date.toISOString();
        $container.attr("data-end-date", newIso);

        // Trigger widget update
        const widgets = this.getPublicWidgets(this.$target);
        if (widgets && widgets.length > 0) {
            const widget = widgets[0];
            widget.endDate = date.getTime();
            widget._updateDisplay(Math.max(0, widget.endDate - new Date().getTime()));
        }
    },

    updateEndTime(previewMode, value) {
        const $container = this.$target.find(".s_deltatech_countdown_container");
        let currentIso = $container.attr("data-end-date");
        let date = currentIso ? new Date(currentIso) : new Date();
        if (isNaN(date.getTime())) date = new Date();

        if (value) {
            const [hours, minutes] = value.split(":").map(Number);
            date.setHours(hours, minutes, 0, 0);
        }
        const newIso = date.toISOString();
        $container.attr("data-end-date", newIso);

        // Trigger widget update
        const widgets = this.getPublicWidgets(this.$target);
        if (widgets && widgets.length > 0) {
            const widget = widgets[0];
            widget.endDate = date.getTime();
            widget._updateDisplay(Math.max(0, widget.endDate - new Date().getTime()));
        }
    },

    toggleConfetti(previewMode, value) {
        const $container = this.$target.find(".s_deltatech_countdown_container");
        $container.attr("data-confetti", value ? "true" : "false");

        // Trigger widget update
        const widgets = this.getPublicWidgets(this.$target);
        if (widgets && widgets.length > 0) {
            widgets[0].confettiTriggered = false; // Allow it to trigger again if it already did
        }
    },
});

export default options.registry.DeltatechCountdownOptions;
