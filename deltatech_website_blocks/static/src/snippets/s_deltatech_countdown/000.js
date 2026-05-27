/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.DeltatechCountdown = publicWidget.Widget.extend({
    selector: ".s_deltatech_countdown",

    init() {
        this._super.apply(this, arguments);
        this.timer = null;
        this.confettiTriggered = false;
    },

    start() {
        if (!this.el) return this._super.apply(this, arguments);
        this.container = this.el.querySelector(".s_deltatech_countdown_container");
        if (!this.container) return this._super.apply(this, arguments);

        if (this.editableMode) {
            this._updateFromDataset();
            return this._super.apply(this, arguments);
        }

        const endDateStr = this.container.getAttribute("data-end-date") || this.container.dataset.endDate;
        if (endDateStr) {
            this.endDate = new Date(endDateStr).getTime();
        } else {
            // Default to 24 hours from now for demo if not set
            this.endDate = new Date().getTime() + 24 * 60 * 60 * 1000;
        }
        this._startTimer();

        return this._super.apply(this, arguments);
    },

    _updateFromDataset() {
        const container = this.el.querySelector(".s_deltatech_countdown_container");
        const endDateStr = container.dataset.endDate || container.getAttribute("data-end-date");
        if (endDateStr) {
            const now = new Date().getTime();
            this.endDate = new Date(endDateStr).getTime();
            const distance = this.endDate - now;
            this._updateDisplay(Math.max(0, distance));
        } else {
            this._updateDisplay(0);
        }
    },

    destroy() {
        this._stopTimer();
        this._super.apply(this, arguments);
    },

    _startTimer() {
        this._stopTimer();
        this._updateTimer();
        this.timer = setInterval(() => this._updateTimer(), 1000);
    },

    _stopTimer() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    },

    _updateTimer() {
        if (!this.el) return;
        const now = new Date().getTime();
        const distance = this.endDate - now;
        const container = this.el.querySelector(".s_deltatech_countdown_container");
        const expiredEl = this.el.querySelector(".s_deltatech_countdown_expired");
        if (!container || !expiredEl) return;

        const confettiAttr = container.dataset.confetti || container.getAttribute("data-confetti");

        if (distance < 0) {
            this._stopTimer();
            this._updateDisplay(0);
            if (!this.editableMode) {
                container.classList.add("d-none");
                expiredEl.classList.remove("d-none");
            }

            if (!this.confettiTriggered && confettiAttr === "true" && !this.editableMode) {
                this._triggerConfetti();
                this.confettiTriggered = true;
            }
            return;
        } else {
            if (!this.editableMode) {
                container.classList.remove("d-none");
                expiredEl.classList.add("d-none");
            }
        }

        this._updateDisplay(distance);
    },

    _updateDisplay(distance) {
        if (!this.el) return;
        const days = Math.floor(distance / (1000 * 60 * 60 * 24));
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);

        const daysEl = this.el.querySelector(".days");
        const hoursEl = this.el.querySelector(".hours");
        const minutesEl = this.el.querySelector(".minutes");
        const secondsEl = this.el.querySelector(".seconds");

        if (daysEl) daysEl.textContent = String(days).padStart(2, "0");
        if (hoursEl) hoursEl.textContent = String(hours).padStart(2, "0");
        if (minutesEl) minutesEl.textContent = String(minutes).padStart(2, "0");
        if (secondsEl) secondsEl.textContent = String(seconds).padStart(2, "0");
    },

    _triggerConfetti() {
        const canvas = document.createElement("canvas");
        canvas.className = "s_deltatech_confetti_canvas";
        document.body.appendChild(canvas);
        const ctx = canvas.getContext("2d");
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        const pieces = [];
        const numberOfPieces = 200;
        const colors = ["#f00", "#0f0", "#00f", "#ff0", "#0ff", "#f0f"];

        for (let i = 0; i < numberOfPieces; i++) {
            pieces.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height - canvas.height,
                rotation: Math.random() * 360,
                color: colors[Math.floor(Math.random() * colors.length)],
                size: Math.random() * 10 + 5,
                speed: Math.random() * 5 + 2,
                oscillation: Math.random() * 0.02,
            });
        }

        function update() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            pieces.forEach((p) => {
                p.y += p.speed;
                p.rotation += p.speed;
                p.x += Math.sin(p.y * p.oscillation);

                ctx.save();
                ctx.translate(p.x, p.y);
                ctx.rotate((p.rotation * Math.PI) / 180);
                ctx.fillStyle = p.color;
                ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
                ctx.restore();
            });

            if (pieces.some((p) => p.y < canvas.height)) {
                requestAnimationFrame(update);
            } else {
                canvas.remove();
            }
        }

        update();
    },
});

export default publicWidget.registry.DeltatechCountdown;
