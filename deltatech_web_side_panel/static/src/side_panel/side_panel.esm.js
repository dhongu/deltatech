/** @odoo-module **/
// ©  2026 Deltatech
// See README.rst file on addons root folder for license details
import {Component, onMounted, onPatched, useExternalListener, useRef, useState, useSubEnv} from "@odoo/owl";
import {View, getDefaultConfig} from "@web/views/view";

export const WIDTH_STORAGE_KEY = "deltatech_web_side_panel.width";
export const MIN_WIDTH = 300;
export const MAX_RATIO = 0.7;
const KEY_STEP = 20;
const KEY_STEP_LARGE = 100;

// Kept in memory too, for the browsers that refuse the local storage.
let memoryWidth = null;

function loadWidth() {
    try {
        const value = parseInt(window.localStorage.getItem(WIDTH_STORAGE_KEY), 10);
        if (value > 0) {
            return value;
        }
    } catch {
        // The storage may be blocked: the width of the session is used.
    }
    return memoryWidth;
}

function saveWidth(width) {
    memoryWidth = width;
    try {
        if (width === null) {
            window.localStorage.removeItem(WIDTH_STORAGE_KEY);
        } else {
            window.localStorage.setItem(WIDTH_STORAGE_KEY, String(width));
        }
    } catch {
        // Not stored: the width stays for this session only.
    }
}

/**
 * The panel shown next to a kanban or a list: the form view of the selected record,
 * read-only, with the buttons to move between records, open the full form, refresh
 * and close.
 */
export class SidePanel extends Component {
    static template = "deltatech_web_side_panel.SidePanel";
    static components = {View};
    static props = {
        resModel: String,
        resId: Number,
        formViewRef: {type: [String, Boolean], optional: true},
        position: Number,
        total: Number,
        onClose: Function,
        onPrev: Function,
        onNext: Function,
        onOpen: Function,
        onRefresh: Function,
    };

    setup() {
        // A view writes into env.config (the breadcrumb title, the views list): give the
        // embedded form its own, so that it leaves the page's breadcrumb alone.
        useSubEnv({config: getDefaultConfig()});
        this.rootRef = useRef("root");
        this.state = useState({width: loadWidth(), current: 0, max: 0, resizing: false});
        useExternalListener(window, "resize", () => this.syncBounds());
        onMounted(() => this.syncBounds());
        // The default width comes from the stylesheet: read it again after each render.
        onPatched(() => this.syncBounds());
    }

    get minWidth() {
        return MIN_WIDTH;
    }

    get rootStyle() {
        // Without a chosen width the default of the stylesheet applies.
        return this.state.width ? `flex-basis: ${this.state.width}px;` : "";
    }

    containerWidth() {
        const parent = this.rootRef.el && this.rootRef.el.parentElement;
        return parent ? parent.clientWidth : 0;
    }

    clampWidth(width) {
        const max = Math.max(MIN_WIDTH, Math.floor(this.containerWidth() * MAX_RATIO));
        return Math.round(Math.min(max, Math.max(MIN_WIDTH, width)));
    }

    syncBounds() {
        const el = this.rootRef.el;
        if (!el) {
            return;
        }
        this.state.current = Math.round(el.getBoundingClientRect().width);
        this.state.max = Math.max(MIN_WIDTH, Math.floor(this.containerWidth() * MAX_RATIO));
    }

    setWidth(width, persist) {
        this.state.width = this.clampWidth(width);
        this.state.current = this.state.width;
        if (persist) {
            saveWidth(this.state.width);
        }
    }

    onResizeStart(ev) {
        if (ev.button !== undefined && ev.button !== 0) {
            return;
        }
        ev.preventDefault();
        try {
            ev.currentTarget.setPointerCapture(ev.pointerId);
        } catch {
            // No active pointer (synthetic event): the move is still followed.
        }
        this.state.resizing = true;
        // The right edge of the panel stays where it is: the width is read from it.
        this.rightEdge = this.rootRef.el.getBoundingClientRect().right;
    }

    onResizeMove(ev) {
        if (this.state.resizing) {
            this.setWidth(this.rightEdge - ev.clientX, false);
        }
    }

    onResizeEnd(ev) {
        if (!this.state.resizing) {
            return;
        }
        this.state.resizing = false;
        try {
            ev.currentTarget.releasePointerCapture(ev.pointerId);
        } catch {
            // Nothing captured.
        }
        saveWidth(this.state.width);
        this.syncBounds();
    }

    onResizeReset() {
        this.state.width = null;
        saveWidth(null);
    }

    onResizeKeydown(ev) {
        const step = ev.shiftKey ? KEY_STEP_LARGE : KEY_STEP;
        const current = this.state.width || this.state.current;
        let target = null;
        if (ev.key === "ArrowLeft") {
            target = current + step;
        } else if (ev.key === "ArrowRight") {
            target = current - step;
        } else if (ev.key === "Home") {
            target = MIN_WIDTH;
        } else if (ev.key === "End") {
            target = Infinity;
        } else {
            return;
        }
        ev.preventDefault();
        this.setWidth(target, true);
    }

    get positionLabel() {
        return `${this.props.position} / ${this.props.total}`;
    }

    get viewProps() {
        // The same object while the record stays: a new one would reload the embedded form
        // each time the panel renders again (for instance when its width changes).
        const {resModel, resId, formViewRef} = this.props;
        const cacheKey = `${resModel}/${resId}/${formViewRef}`;
        if (this._viewPropsKey !== cacheKey) {
            this._viewPropsKey = cacheKey;
            this._viewProps = this.computeViewProps();
        }
        return this._viewProps;
    }

    computeViewProps() {
        const context = {};
        if (this.props.formViewRef) {
            // Odoo resolves the xml id of the form view on the server.
            context.form_view_ref = this.props.formViewRef;
        }
        return {
            type: "form",
            resModel: this.props.resModel,
            resId: this.props.resId,
            context,
            display: {controlPanel: false},
            readonly: true,
        };
    }
}
