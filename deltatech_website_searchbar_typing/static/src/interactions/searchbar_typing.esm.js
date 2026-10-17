import {Interaction} from "@web/public/interaction";
import {registry} from "@web/core/registry";

/**
 * The placeholder of a website search box types example searches, one after
 * another: typed letter by letter, held, erased, then the next one.
 *
 * It runs only on the search forms that carry the examples, as translatable text:
 *
 *     <ul class="o_searchbar_typing d-none" aria-hidden="true">
 *         <li class="o_searchbar_typing_prefix">e.g.</li>
 *         <li>first example</li>
 *         <li>second example</li>
 *     </ul>
 *
 * Block elements (li) make each example a translation term of its own; inline
 * elements (span) would be translated as one block of HTML.
 *
 * It stops for good when the visitor focuses the box or types, and gives back the
 * original placeholder. It waits while the tab is hidden or the box is out of view,
 * and it does not run with prefers-reduced-motion. Public interactions do not run
 * in the Website Builder.
 */
export class SearchbarTyping extends Interaction {
    static selector = ".o_searchbar_form";
    static selectorHas = ".o_searchbar_typing";

    dynamicContent = {
        ".search-query": {
            "t-on-focus": this.halt,
            "t-on-input": this.halt,
        },
    };

    setup() {
        this.inputEl = this.el.querySelector(".search-query");
        const boxEl = this.el.querySelector(".o_searchbar_typing");
        const prefixEl = boxEl.querySelector(".o_searchbar_typing_prefix");
        // The prefix is separated from the example by a space.
        const prefix = prefixEl ? prefixEl.textContent.trim() : "";
        this.prefix = prefix ? `${prefix} ` : "";
        this.examples = [...boxEl.children]
            .filter((el) => el !== prefixEl)
            .map((el) => el.textContent.trim())
            .filter(Boolean);
        const data = boxEl.dataset;
        this.delays = {
            start: parseInt(data.startDelay, 10) || 1500,
            type: parseInt(data.typeDelay, 10) || 70,
            hold: parseInt(data.holdDelay, 10) || 1800,
            erase: parseInt(data.eraseDelay, 10) || 30,
            next: parseInt(data.nextDelay, 10) || 400,
        };
        this.basePlaceholder = this.inputEl ? this.inputEl.getAttribute("placeholder") || "" : "";
        this.wordIndex = 0;
        this.charCount = 0;
        this.erasing = false;
        this.stopped = false;
        this.visible = false;
        this.timer = null;
    }

    start() {
        if (!this.inputEl || !this.examples.length || this.inputEl.value) {
            return;
        }
        // Screen readers would read every changed letter as the name of the box.
        const labelled =
            this.inputEl.hasAttribute("aria-label") ||
            this.inputEl.hasAttribute("aria-labelledby") ||
            (this.inputEl.id && this.el.querySelector(`label[for="${this.inputEl.id}"]`));
        if (!labelled && this.basePlaceholder) {
            this.inputEl.setAttribute("aria-label", this.basePlaceholder);
            this.registerCleanup(() => this.inputEl.removeAttribute("aria-label"));
        }
        this.motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
        this.addListener(this.motionQuery, "change", this.sync);
        this.addListener(document, "visibilitychange", this.sync);
        if ("IntersectionObserver" in window) {
            const observer = new IntersectionObserver((entries) => {
                this.visible = entries[entries.length - 1].isIntersecting;
                this.sync();
            });
            observer.observe(this.inputEl);
            this.registerCleanup(() => observer.disconnect());
        } else {
            this.visible = true;
            this.sync();
        }
    }

    destroy() {
        this.pause();
    }

    get canRun() {
        return !this.stopped && this.visible && !document.hidden && !this.motionQuery.matches;
    }

    /**
     * Starts or pauses the animation after any change of its conditions. A paused
     * animation shows the original placeholder and starts the current example again.
     */
    sync() {
        if (!this.canRun) {
            this.pause();
        } else if (!this.timer) {
            this.schedule(this.delays.start);
        }
    }

    pause() {
        clearTimeout(this.timer);
        this.timer = null;
        this.charCount = 0;
        this.erasing = false;
        if (this.inputEl) {
            this.inputEl.setAttribute("placeholder", this.basePlaceholder);
        }
    }

    halt() {
        this.stopped = true;
        this.pause();
    }

    schedule(delay) {
        this.timer = this.waitForTimeout(this.tick, delay);
    }

    tick() {
        const word = this.examples[this.wordIndex];
        this.charCount += this.erasing ? -1 : 1;
        this.inputEl.setAttribute("placeholder", this.prefix + word.slice(0, this.charCount));
        let delay = this.erasing ? this.delays.erase : this.delays.type;
        if (!this.erasing && this.charCount >= word.length) {
            this.erasing = true;
            delay = this.delays.hold;
        } else if (this.erasing && this.charCount <= 0) {
            this.erasing = false;
            this.wordIndex = (this.wordIndex + 1) % this.examples.length;
            delay = this.delays.next;
        }
        this.schedule(delay);
    }
}

registry.category("public.interactions").add("deltatech_website_searchbar_typing.searchbar_typing", SearchbarTyping);
