import {Component, onMounted, proxy, t, usePlugin, useProps} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {useHotkey} from "@web/core/hotkeys/hotkey_hook";
import {useService} from "@web/core/utils/hooks";
import {ActionPlugin} from "@web/webclient/actions/action_plugin";

// Item status: "pending" (not run yet), "running" (RPC in flight), "success", "warning"
// (done, with a result to check by hand: never run again) and "error" (run again by retry).
const DONE = ["success", "warning"];

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
 * What a step returned: a number is the count of a successful item, an object can also
 * give its status and a message.
 */
export function stepResult(result) {
    if (result && typeof result === "object") {
        return {
            status: ["warning", "error"].includes(result.status) ? result.status : "success",
            message: result.message || "",
            count: typeof result.count === "number" ? result.count : 0,
        };
    }
    return {status: "success", message: "", count: typeof result === "number" ? result : 0};
}

function errorMessage(error) {
    return (error && error.data && error.data.message) || (error && error.message) || String(error);
}

/**
 * Runs a long task item by item (one RPC and one transaction per item, a few at a time),
 * shows the progress, then calls the finish method and opens the action it returns.
 * A failed item can be run again; finish is called only when every item is done, so
 * nothing is silently missing. Opened by task.progress.mixin._task_progress_action.
 */
export class TaskProgressDialog extends Component {
    static template = "deltatech_task_progress.TaskProgressDialog";
    static components = {Dialog};
    props = useProps({
        title: t.string(),
        model: t.string(),
        resId: t.or([t.number(), t.boolean()]),
        step: t.string(),
        init: t.or([t.string(), t.literal(null)]).optional(),
        finish: t.or([t.string(), t.literal(null)]).optional(),
        finishMode: t.string(),
        closeMethod: t.or([t.string(), t.literal(null)]).optional(),
        items: t.array(),
        itemNames: t.array(),
        total: t.number(),
        parallel: t.number(),
        autoStart: t.boolean(),
        showItems: t.boolean(),
        intro: t.string(),
        unitLabel: t.string(),
        countLabel: t.string(),
        detail: t.string(),
        labels: t.object(),
        close: t.function(),
    });

    setup() {
        this.orm = useService("orm");
        this.action = usePlugin(ActionPlugin);
        this.state = proxy({
            rows: [],
            before: 0,
            total: 0,
            detail: this.props.detail,
            count: 0,
            started: false,
            preparing: Boolean(this.props.init),
            running: false,
            stopping: false,
            finishing: false,
            finished: false,
            fatal: "",
            etaSeconds: null,
        });
        this.setItems(this.props.items, this.props.itemNames, this.props.total);
        // Closing while running would leave items not done
        useHotkey("escape", () => undefined, {isAvailable: () => this.busy});
        onMounted(() => this.open());
    }

    setItems(items, names, total) {
        this.state.rows = items.map((item, i) => ({
            item,
            name: (names && names[i]) || String(item),
            status: "pending",
            message: "",
        }));
        this.state.total = typeof total === "number" ? total : items.length;
        this.state.before = this.state.total - items.length;
    }

    async open() {
        if (this.props.init) {
            try {
                const plan = await this.orm.call(this.props.model, this.props.init, [[this.props.resId]]);
                this.setItems(plan.items || [], plan.item_names, plan.total);
                if (plan.detail) {
                    this.state.detail = plan.detail;
                }
            } catch (error) {
                this.state.fatal = errorMessage(error);
                return;
            } finally {
                this.state.preparing = false;
            }
        }
        if (this.props.autoStart) {
            await this.run();
        }
    }

    get labels() {
        return {
            running: _t("Running..."),
            finishing: _t("Finishing..."),
            preparing: _t("Preparing..."),
            stop: _t("Stop after the current items"),
            retry: _t("Run the remaining items"),
            start: _t("Start"),
            finish: _t("Finish"),
            ...this.props.labels,
        };
    }

    get busy() {
        return this.state.preparing || this.state.running || this.state.finishing;
    }

    get doneRows() {
        return this.state.rows.filter((row) => DONE.includes(row.status));
    }

    get failedRows() {
        return this.state.rows.filter((row) => row.status === "error");
    }

    get remainingRows() {
        return this.state.rows.filter((row) => !DONE.includes(row.status));
    }

    get doneCount() {
        return this.state.before + this.doneRows.length;
    }

    get progressPercent() {
        if (!this.state.total) {
            return this.state.preparing ? 0 : 100;
        }
        return Math.min(100, Math.round((this.doneCount / this.state.total) * 100));
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
            done: this.doneCount,
            total: this.state.total,
            unit: this.props.unitLabel,
        }).trim();
        if (this.state.detail) {
            label += ` (${this.state.detail})`;
        }
        if (this.props.countLabel) {
            label += ` — ${this.state.count} ${this.props.countLabel}`;
        }
        return label;
    }

    get errorsLabel() {
        return _t("%(count)s item(s) failed. Run them again to continue.", {
            count: this.failedRows.length,
        });
    }

    get warningsCount() {
        return this.state.rows.filter((row) => row.status === "warning").length;
    }

    get errors() {
        return this.failedRows.map((row) => _t("%(item)s: %(message)s", {item: row.name, message: row.message}));
    }

    get statusLabel() {
        if (this.state.preparing) {
            return this.labels.preparing;
        }
        if (this.state.finishing) {
            return this.labels.finishing;
        }
        if (this.state.running) {
            return this.labels.running;
        }
        if (this.state.fatal || this.failedRows.length) {
            return _t("Not finished");
        }
        if (!this.state.started) {
            return "";
        }
        if (this.state.stopping) {
            return _t("Stopped");
        }
        return _t("Done");
    }

    get canStart() {
        return !this.state.started && !this.busy && !this.state.fatal && this.state.rows.length > 0;
    }

    get canRetry() {
        return this.state.started && !this.busy && this.remainingRows.length > 0;
    }

    get canFinish() {
        return (
            this.props.finish &&
            this.props.finishMode === "button" &&
            this.state.started &&
            !this.busy &&
            this.doneRows.length > 0
        );
    }

    async run() {
        this.state.started = true;
        this.state.running = true;
        this.state.stopping = false;
        const queue = this.remainingRows;
        const startTime = Date.now();
        const toRun = queue.length;
        let doneHere = 0;
        const worker = async () => {
            while (queue.length && !this.state.stopping) {
                const row = queue.shift();
                row.status = "running";
                row.message = "";
                try {
                    // On a record: record.step(item); without one: model.browse(item).step()
                    const args = this.props.resId ? [[this.props.resId], row.item] : [[row.item]];
                    const result = stepResult(await this.orm.call(this.props.model, this.props.step, args));
                    row.status = result.status;
                    row.message = result.message;
                    this.state.count += result.count;
                } catch (error) {
                    row.status = "error";
                    row.message = errorMessage(error);
                }
                doneHere++;
                const elapsed = (Date.now() - startTime) / 1000;
                this.state.etaSeconds = (elapsed / doneHere) * (toRun - doneHere);
            }
            // Stopped: the items not taken stay pending, ready for the retry
        };
        const workers = Math.max(1, Math.min(this.props.parallel, queue.length));
        await Promise.all(Array.from({length: workers}, () => worker()));
        this.state.running = false;
        if (!this.remainingRows.length && !this.state.stopping && this.props.finishMode === "auto") {
            await this.finish();
        }
    }

    async finish() {
        if (!this.props.finish) {
            this.state.finished = true;
            return;
        }
        this.state.finishing = true;
        try {
            const args = this.props.resId ? [[this.props.resId]] : [this.doneRows.map((row) => row.item)];
            const action = await this.orm.call(this.props.model, this.props.finish, args);
            this.state.finished = true;
            if (this.props.finishMode === "auto" || (action && action.type === "ir.actions.act_window")) {
                this.props.close();
            }
            if (action) {
                await this.action.doAction(withViews(action));
            }
        } catch (error) {
            this.state.fatal = errorMessage(error);
        } finally {
            this.state.finishing = false;
        }
    }

    async closeDialog() {
        const complete = this.state.started && !this.remainingRows.length;
        if (this.props.closeMethod && complete) {
            const action = await this.orm.call(this.props.model, this.props.closeMethod, [[this.props.resId]]);
            this.props.close();
            if (action) {
                await this.action.doAction(withViews(action));
            }
            return;
        }
        this.props.close();
    }

    stop() {
        this.state.stopping = true;
    }

    retry() {
        this.state.fatal = "";
        this.run();
    }
}

async function taskProgressAction(env, action) {
    const params = action.params || {};
    env.services.dialog.add(TaskProgressDialog, {
        title: params.title || "",
        model: params.model,
        resId: params.res_id || false,
        step: params.step,
        init: params.init || null,
        finish: params.finish || null,
        finishMode: params.finish_mode || "auto",
        closeMethod: params.close || null,
        items: params.items || [],
        itemNames: params.item_names || [],
        total: typeof params.total === "number" ? params.total : (params.items || []).length,
        parallel: params.parallel || 1,
        autoStart: params.auto_start !== false,
        showItems: Boolean(params.show_items),
        intro: params.intro || "",
        unitLabel: params.unit_label || "",
        countLabel: params.count_label || "",
        detail: params.detail || "",
        labels: params.labels || {},
    });
}

registry.category("actions").add("deltatech_task_progress.run", taskProgressAction);
