# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTaskProgress(TransactionCase):
    def setUp(self):
        super().setUp()
        self.record = self.env["task.progress.mixin"].browse(7)

    def test_action(self):
        action = self.record._task_progress_action(
            "run_part",
            [0, 1, 2],
            finish="action_done",
            parallel=2,
            title="Reading",
            unit_label="parts",
            count_label="lines",
            detail="3 pages",
            labels={"running": "Reading..."},
        )
        self.assertEqual(action["type"], "ir.actions.client")
        self.assertEqual(action["tag"], "deltatech_task_progress.run")
        params = action["params"]
        self.assertEqual(params["model"], "task.progress.mixin")
        self.assertEqual(params["res_id"], 7)
        self.assertEqual(params["step"], "run_part")
        self.assertEqual(params["finish"], "action_done")
        self.assertEqual(params["items"], [0, 1, 2])
        self.assertEqual(params["item_names"], ["0", "1", "2"], "Items named by their value by default")
        self.assertEqual(params["total"], 3)
        self.assertEqual(params["parallel"], 2)
        self.assertEqual(params["labels"], {"running": "Reading..."})

    def test_resumed_task(self):
        action = self.record._task_progress_action("run_part", [2], total=3, item_names=["Part 3"], parallel=0)
        params = action["params"]
        self.assertEqual(params["total"], 3, "The items done before count in the progress")
        self.assertEqual(params["item_names"], ["Part 3"])
        self.assertEqual(params["parallel"], 1, "At least one item at a time")
        self.assertIsNone(params["finish"])
        self.assertEqual(params["labels"], {})

    def test_batches_of_ids(self):
        action = self.record._task_progress_action("run_batch", iter([[1, 2], [3]]))
        self.assertEqual(action["params"]["items"], [[1, 2], [3]], "Any iterable, read once")
        self.assertEqual(action["params"]["total"], 2)

    def test_items_without_record(self):
        mixin = self.env["task.progress.mixin"]
        action = mixin._task_progress_action(
            "action_send",
            [3, 5],
            model="res.partner",
            item_names=["A", "B"],
            finish="action_print",
            finish_mode="button",
            auto_start=False,
            show_items=True,
            intro="Send 2 orders",
        )
        params = action["params"]
        self.assertEqual(params["model"], "res.partner", "The steps run on the item records")
        self.assertIs(params["res_id"], False)
        self.assertEqual(params["finish_mode"], "button")
        self.assertFalse(params["auto_start"])
        self.assertTrue(params["show_items"])
        self.assertEqual(params["intro"], "Send 2 orders")

    def test_init_prepares_the_items(self):
        action = self.record._task_progress_action("run_batch", init="action_plan", close="action_open")
        params = action["params"]
        self.assertEqual((params["init"], params["close"]), ("action_plan", "action_open"))
        self.assertEqual(params["items"], [], "The items come from init")
        self.assertTrue(params["auto_start"])
        self.assertEqual(params["finish_mode"], "auto")

    def test_invalid_calls(self):
        mixin = self.env["task.progress.mixin"]
        with self.assertRaises(ValueError):
            mixin._task_progress_action("step", [1])
        with self.assertRaises(ValueError):
            mixin._task_progress_action("step", [1], model="res.partner", init="action_plan")
        with self.assertRaises(ValueError):
            self.record._task_progress_action("step", [1], finish_mode="later")
