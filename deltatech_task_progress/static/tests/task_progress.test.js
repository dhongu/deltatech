import {describe, expect, test} from "@odoo/hoot";
import {animationFrame, queryAll, queryOne} from "@odoo/hoot-dom";
import {contains, defineModels, getService, models, mountWithCleanup, onRpc} from "@web/../tests/web_test_helpers";
import {WebClient} from "@web/webclient/webclient";
import {stepResult, withViews} from "@deltatech_task_progress/task_progress/task_progress.esm";

class TaskWizard extends models.Model {
    _name = "task.wizard";
    _records = [{id: 1}];
}

defineModels([TaskWizard]);

function progressAction(params = {}) {
    return {
        type: "ir.actions.client",
        tag: "deltatech_task_progress.run",
        params: {
            model: "task.wizard",
            res_id: 1,
            step: "run_part",
            finish: "action_done",
            items: [0, 1, 2],
            item_names: ["Part 1", "Part 2", "Part 3"],
            total: 3,
            parallel: 2,
            title: "Reading",
            unit_label: "parts",
            count_label: "lines",
            ...params,
        },
    };
}

describe("withViews", () => {
    test("adds the views of a window action", () => {
        expect(withViews({type: "ir.actions.act_window", view_mode: "form"}).views).toEqual([[false, "form"]]);
        expect(withViews({type: "ir.actions.act_window", view_mode: "list,form", view_id: [5, "v"]}).views).toEqual([
            [5, "list"],
            [false, "form"],
        ]);
        const action = {type: "ir.actions.act_window", views: [[3, "form"]]};
        expect(withViews(action)).toBe(action);
        expect(withViews({type: "ir.actions.client"}).views).toBe(undefined);
    });
});

describe("stepResult", () => {
    test("reads a count or a status", () => {
        expect(stepResult(4)).toEqual({status: "success", message: "", count: 4});
        expect(stepResult(null)).toEqual({status: "success", message: "", count: 0});
        expect(stepResult({status: "warning", message: "check"})).toEqual({
            status: "warning",
            message: "check",
            count: 0,
        });
        expect(stepResult({status: "odd", count: 2}).status).toBe("success");
    });
});

describe("TaskProgressDialog", () => {
    test("runs every item, then calls finish", async () => {
        onRpc("task.wizard", "run_part", ({args}) => {
            expect.step(`part ${args[1]}`);
            return 2;
        });
        onRpc("task.wizard", "action_done", () => {
            expect.step("finish");
            return false;
        });
        await mountWithCleanup(WebClient);
        await getService("action").doAction(progressAction());
        await animationFrame();
        await expect.waitForSteps(["part 0", "part 1", "part 2", "finish"]);
        await animationFrame();
        expect(".modal").toHaveCount(0);
    });

    test("a failed item is shown and run again alone", async () => {
        let fail = true;
        onRpc("task.wizard", "run_part", ({args}) => {
            expect.step(`part ${args[1]}`);
            if (args[1] === 1 && fail) {
                fail = false;
                throw new Error("timeout");
            }
            return 3;
        });
        onRpc("task.wizard", "action_done", () => {
            expect.step("finish");
            return false;
        });
        await mountWithCleanup(WebClient);
        await getService("action").doAction(progressAction({parallel: 1}));
        await expect.waitForSteps(["part 0", "part 1", "part 2"]);
        await animationFrame();
        expect(queryAll(".o_task_progress_error")).toHaveLength(1);
        expect(queryOne(".o_task_progress_error").textContent).toMatch(/^Part 2: /);
        expect(".o_task_progress_counter").toHaveText("2 / 3 parts — 6 lines");
        await contains(".o_task_progress_retry").click();
        await expect.waitForSteps(["part 1", "finish"]);
    });

    test("items without a record: list, start button, warning kept, finish button", async () => {
        onRpc("task.wizard", "send", ({args}) => {
            const id = args[0][0];
            expect.step(`send ${id}`);
            if (id === 2) {
                return {status: "warning", message: "uncertain"};
            }
            if (id === 3) {
                return {status: "error", message: "no carrier"};
            }
            return {status: "success", message: "AWB 123"};
        });
        onRpc("task.wizard", "print", ({args}) => {
            expect.step(`print ${args[0].join(",")}`);
            return false;
        });
        await mountWithCleanup(WebClient);
        await getService("action").doAction(
            progressAction({
                res_id: false,
                step: "send",
                finish: "print",
                finish_mode: "button",
                items: [1, 2, 3],
                item_names: ["S1", "S2", "S3"],
                auto_start: false,
                show_items: true,
                intro: "Send 3 orders",
                labels: {start: "Send", finish: "Print"},
            })
        );
        await animationFrame();
        expect(".o_task_progress_intro").toHaveText("Send 3 orders");
        expect(".o_task_progress_items tr").toHaveCount(3);
        expect.verifySteps([]);
        await contains(".o_task_progress_start").click();
        await expect.waitForSteps(["send 1", "send 2", "send 3"]);
        await animationFrame();
        expect(".o_task_progress_item_success").toHaveText("S1 AWB 123");
        expect(".o_task_progress_item_warning").toHaveText("S2 uncertain");
        expect(".o_task_progress_item_error").toHaveText("S3 no carrier");
        await contains(".o_task_progress_finish").click();
        await expect.waitForSteps(["print 1,2"]);
        expect(".modal").toHaveCount(1, {message: "The dialog stays open after the button"});
        await contains(".o_task_progress_retry").click();
        await expect.waitForSteps(["send 3"]);
    });

    test("init prepares the items, close opens an action", async () => {
        onRpc("task.wizard", "plan", async () => {
            expect.step("plan");
            expect(".o_task_progress_state").toHaveText("Preparing...");
            expect(".o_task_progress_counter").toHaveCount(0, {message: "No counter before the items"});
            return {items: [0, 10], item_names: ["Batch 1", "Batch 2"], total: 2, detail: "20 rows"};
        });
        onRpc("task.wizard", "run_part", ({args}) => {
            expect.step(`part ${args[1]}`);
            return 10;
        });
        onRpc("task.wizard", "open_form", () => {
            expect.step("close");
            return false;
        });
        await mountWithCleanup(WebClient);
        await getService("action").doAction(
            progressAction({items: [], total: 0, init: "plan", finish: false, close: "open_form", parallel: 1})
        );
        await expect.waitForSteps(["plan", "part 0", "part 10"]);
        await animationFrame();
        expect(".o_task_progress_counter").toHaveText("2 / 2 parts (20 rows) — 20 lines");
        await contains(".o_task_progress_close").click();
        await expect.waitForSteps(["close"]);
    });
});
