import {describe, expect, test} from "@odoo/hoot";
import {animationFrame, queryAll, queryOne} from "@odoo/hoot-dom";
import {contains, defineModels, getService, models, mountWithCleanup, onRpc} from "@web/../tests/web_test_helpers";
import {WebClient} from "@web/webclient/webclient";
import {withViews} from "@deltatech_task_progress/task_progress/task_progress.esm";

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
});
