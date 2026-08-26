/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.StatsCounters = publicWidget.Widget.extend({
    selector: ".s_deltatech_stats_counters",

    /**
     * @override
     */
    start: function () {
        this.hasRun = false;
        this.GLOBAL_DURATION_MS = 5200;
        this.LOOP_PAUSE_MS = 900;
        this.FADE_OUT_MS = 450;
        this.RESTART_DELAY_MS = 250;
        this.timeouts = [];

        this.initAnimation();
        return this._super.apply(this, arguments);
    },

    destroy: function () {
        if (this.observer) {
            this.observer.disconnect();
        }
        this.timeouts.forEach(clearTimeout);
        this._super.apply(this, arguments);
    },

    initAnimation: function () {
        if (!this.el) return;
        if (this.el.closest(".editor_enable") || this.el.closest(".o_editable_auto_status")) {
            // In editor mode, set counters to their target values without animation
            this.setCountersToTarget();
            return;
        }

        this.observer = new IntersectionObserver(
            (entries) => {
                for (const entry of entries) {
                    if (entry.isIntersecting) {
                        this.startAnimationLoop();
                        this.observer.disconnect();
                        this.observer = null;
                    }
                }
            },
            {
                threshold: 0.05,
                rootMargin: "0px 0px -5% 0px",
            }
        );
        this.observer.observe(this.el);
    },

    setCountersToTarget: function () {
        this.el.querySelectorAll(".count").forEach((el) => {
            const target = Number(el.dataset.target || 0);
            const mode = el.dataset.format || "plain";
            el.textContent = this.formatNumber(target, mode);
        });
    },

    formatNumber: function (n, mode) {
        if (mode === "group") {
            return Math.round(n).toLocaleString("en-US");
        }
        return String(Math.round(n));
    },

    startAnimationLoop: function () {
        if (this.hasRun) return;
        this.hasRun = true;

        const counters = Array.from(this.el.querySelectorAll(".count")).map((el) => ({
            el: el,
            valueEl: el.closest(".value"),
            target: Number(el.dataset.target || 0),
            mode: el.dataset.format || "plain",
        }));

        const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);

        const setAllTo = (multiplier) => {
            for (const c of counters) {
                c.el.textContent = this.formatNumber(c.target * multiplier, c.mode);
            }
        };

        const fadeOutAll = () => {
            for (const c of counters) {
                if (c.valueEl) {
                    c.valueEl.classList.add("is-fading-out");
                }
            }
        };

        const fadeInAll = () => {
            for (const c of counters) {
                if (c.valueEl) {
                    c.valueEl.classList.remove("is-fading-out");
                }
            }
        };

        const runCycle = () => {
            // Check if we are still in the DOM and NOT in editor mode
            if (!this.el || this.el.closest(".editor_enable") || this.el.closest(".o_editable_auto_status")) return;

            fadeInAll();
            setAllTo(0);

            const start = performance.now();

            const frame = (now) => {
                if (!this.el || this.el.closest(".editor_enable") || this.el.closest(".o_editable_auto_status")) return;

                const t = Math.min(1, (now - start) / this.GLOBAL_DURATION_MS);
                const k = easeOutCubic(t);

                for (const c of counters) {
                    c.el.textContent = this.formatNumber(c.target * k, c.mode);
                }

                if (t < 1) {
                    requestAnimationFrame(frame);
                } else {
                    for (const c of counters) {
                        c.el.textContent = this.formatNumber(c.target, c.mode);
                    }

                    this.timeouts.push(
                        setTimeout(() => {
                            if (
                                !this.el ||
                                this.el.closest(".editor_enable") ||
                                this.el.closest(".o_editable_auto_status")
                            )
                                return;
                            fadeOutAll();

                            this.timeouts.push(
                                setTimeout(() => {
                                    if (
                                        !this.el ||
                                        this.el.closest(".editor_enable") ||
                                        this.el.closest(".o_editable_auto_status")
                                    )
                                        return;
                                    setAllTo(0);

                                    requestAnimationFrame(() => {
                                        if (
                                            !this.el ||
                                            this.el.closest(".editor_enable") ||
                                            this.el.closest(".o_editable_auto_status")
                                        )
                                            return;
                                        fadeInAll();

                                        this.timeouts.push(
                                            setTimeout(() => {
                                                runCycle();
                                            }, this.RESTART_DELAY_MS)
                                        );
                                    });
                                }, this.FADE_OUT_MS)
                            );
                        }, this.LOOP_PAUSE_MS)
                    );
                }
            };

            requestAnimationFrame(frame);
        };

        runCycle();
    },
});

export default publicWidget.registry.StatsCounters;
