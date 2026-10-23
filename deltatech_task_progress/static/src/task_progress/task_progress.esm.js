import {Component, onMounted, useState} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {useHotkey} from "@web/core/hotkeys/hotkey_hook";
import {useService} from "@web/core/utils/hooks";

/**
 * The action a method returns over RPC skips the server-side clean-up a button's result
 * goes through: a window action has no `views`, which the web client needs.
 */
export function withViews(action) {
    if (!action || action.type !== "ir.actions.act_window" || action.views) {
        return action;
    }
    const viewId = Array.isArray(action.view_id) ? action.view_id[0] : action.view_id || false;
    const modes = (action.view_mode || "list,form").split(",");
    return {...action, views: modes.map((mode, i) => [i === 0 ? viewId : false, mode])};
}

/**
 * Runs a long task item by item (one RPC and one transaction per item, a few at a time),
 * shows the progress, then calls the finish method and opens the action it returns.
 * A failed item can be run again; finish is called only when every item is done, so
 * nothing is silently missing. Opened by task.progress.mixin._task_progress_action.
 */
export class TaskProgressDialog extends Component {
    static get template() {
        return "deltatech_task_progress.TaskProgressDialog";
    }
    static get components() {
        return {Dialog};
    }
    static get props() {
        return {
            title: String,
            model: String,
            resId: Number,
            step: String,
            finish: {type: [String, {value: null}], optional: true},
            items: Array,
            itemNames: Array,
            total: Number,
            parallel: Number,
            unitLabel: String,
            countLabel: String,
            detail: String,
            labels: Object,
            close: Function,
        };
    }

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.names = new Map(this.props.items.map((item, i) => [JSON.stringify(item), this.props.itemNames[i]]));
        this.state = useState({
            pending: [...this.props.items],
            done: this.props.total - this.props.items.length,
            count: 0,
            errors: [],
            failed: [],
            running: false,
            stopping: false,
            finishing: false,
            etaSeconds: null,
        });
        // Closing while running would leave items not done
        useHotkey("escape", () => undefined, {isAvailable: () => this.state.running});
        onMounted(() => this.run());
    }

    get labels() {
        return {
            running: _t("Running..."),
            finishing: _t("Finishing..."),
            stop: _t("Stop after the current items"),
            retry: _t("Run the remaining items"),
            ...this.props.labels,
        };
    }

    get progressPercent() {
        if (!this.props.total) {
            return 100;
        }
        return Math.min(100, Math.round((this.state.done / this.props.total) * 100));
    }

    get etaLabel() {
        const s = this.state.etaSeconds;
        if (s === null || s <= 0) {
            return "";
        }
        if (s < 60) {
            return _t("~%(seconds)ss left", {seconds: Math.round(s)});
        }
        return _t("~%(minutes)smin left", {minutes: Math.round(s / 60)});
    }

    get counterLabel() {
        let label = _t("%(done)s / %(total)s %(unit)s", {
            done: this.state.done,
            total: this.props.total,
            unit: this.props.unitLabel,
        }).trim();
        if (this.props.detail) {
            label += ` (${this.props.detail})`;
        }
        if (this.props.countLabel) {
            label += ` — ${this.state.count} ${this.props.countLabel}`;
        }
        return label;
    }

    get errorsLabel() {
        return _t("%(count)s item(s) failed. Run them again to continue.", {
            count: this.state.failed.length,
        });
    }

    itemName(item) {
        return this.names.get(JSON.stringify(item)) || String(item);
    }

    async run() {
        this.state.running = true;
        this.state.errors = [];
        this.state.failed = [];
        const queue = [...this.state.pending];
        const startTime = Date.now();
        const toRun = queue.length;
        let doneHere = 0;
        const worker = async () => {
            while (queue.length && !this.state.stopping) {
                const item = queue.shift();
                try {
                    const result = await this.orm.call(this.props.model, this.props.step, [[this.props.resId], item]);
                    this.state.count += typeof result === "number" ? result : 0;
                    this.state.done++;
                    this.state.pending = this.state.pending.filter((i) => i !== item);
                } catch (error) {
                    const message = (error.data && error.data.message) || error.message || String(error);
                    this.state.failed.push(item);
                    this.state.errors.push(_t("%(item)s: %(message)s", {item: this.itemName(item), message}));
                }
                doneHere++;
                const elapsed = (Date.now() - startTime) / 1000;
                this.state.etaSeconds = (elapsed / doneHere) * (toRun - doneHere);
            }
        };
        const workers = Math.max(1, Math.min(this.props.parallel, queue.length));
        await Promise.all(Array.from({length: workers}, () => worker()));
        this.state.running = false;
        if (!this.state.pending.length && !this.state.stopping) {
            await this.finish();
        }
    }

    async finish() {
        if (!this.props.finish) {
            return;
        }
        this.state.finishing = true;
        const action = await this.orm.call(this.props.model, this.props.finish, [[this.props.resId]]);
        this.props.close();
        if (action) {
            await this.action.doAction(withViews(action));
        }
    }

    stop() {
        this.state.stopping = true;
    }

    retry() {
        this.state.stopping = false;
        this.run();
    }
}

async function taskProgressAction(env, action) {
    const params = action.params || {};
    env.services.dialog.add(TaskProgressDialog, {
        title: params.title || "",
        model: params.model,
        resId: params.res_id,
        step: params.step,
        finish: params.finish || null,
        items: params.items || [],
        itemNames: params.item_names || [],
        total: params.total || 0,
        parallel: params.parallel || 1,
        unitLabel: params.unit_label || "",
        countLabel: params.count_label || "",
        detail: params.detail || "",
        labels: params.labels || {},
    });
}

registry.category("actions").add("deltatech_task_progress.run", taskProgressAction);
