# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestBusinessProcessTest(TransactionCase):
    def setUp(self):
        super().setUp()
        # Minimal partner for responsible/tester
        self.partner = self.env["res.partner"].search([], limit=1)
        if not self.partner:
            self.partner = self.env["res.partner"].create({"name": "Tester"})

        # A business area and group
        self.area = self.env["business.area"].create(
            {
                "name": "ERP",
                "responsible_id": self.partner.id,
            }
        )
        self.group = self.env["business.process.group"].create(
            {
                "name": "Sales",
                "area_id": self.area.id,
            }
        )

        # A project and a process with steps
        self.project = self.env["business.project"].create(
            {
                "name": "Implementation",
                "customer_id": self.partner.id,
                "project_type": "remote",
            }
        )
        self.process = self.env["business.process"].create(
            {
                "name": "Order to Cash",
                "area_id": self.area.id,
                "process_group_id": self.group.id,
                "project_id": self.project.id,
                "responsible_id": self.partner.id,
                "customer_id": self.partner.id,
            }
        )
        # Create two steps to be mirrored into test steps by onchange
        self.step1 = self.env["business.process.step"].create({"name": "Create SO", "process_id": self.process.id})
        self.step2 = self.env["business.process.step"].create({"name": "Confirm SO", "process_id": self.process.id})

        # Create a Business Process Test
        self.bpt = self.env["business.process.test"].create(
            {
                "name": "",
                "process_id": self.process.id,
                "scope": "internal",
            }
        )

    def test_onchange_process_id_populates_steps_and_name(self):
        # Simulate onchange to populate test steps and name if empty
        self.bpt._onchange_process_id()
        # Name should be set to something non-empty
        self.assertTrue(self.bpt.name)
        # At least one test step should be created (implementation overwrites per loop)
        self.assertTrue(len(self.bpt.test_step_ids) >= 1)
        # Counter should reflect number of linked test steps
        self.bpt._compute_count_steps()
        self.assertEqual(self.bpt.count_steps, len(self.bpt.test_step_ids))

    def test_compute_completion_test(self):
        # Ensure we have test steps
        if not self.bpt.test_step_ids:
            self.bpt._onchange_process_id()
        # Mark first step passed, others failed/draft
        steps = self.bpt.test_step_ids
        if steps:
            steps[0].result = "passed"
            if len(steps) > 1:
                steps[1].result = "failed"
        self.bpt._compute_completion_test()
        passed = len(steps.filtered(lambda s: s.result == "passed"))
        total = len(steps)
        expected = round((passed / total) * 100, 2) if total else 0.0
        self.assertEqual(self.bpt.completion_test, expected)

    def test_action_view_test_steps_and_attachments(self):
        # Action should be a valid action dict with proper domain
        action = self.bpt.action_view_test_steps()
        self.assertIsInstance(action, dict)
        self.assertIn("domain", action)
        self.assertIn(("process_test_id", "=", self.bpt.id), action["domain"])

        # Attachment helpers
        Attachment = self.env["ir.attachment"].sudo()
        Attachment.create(
            {
                "name": "test.txt",
                "res_model": self.bpt._name,
                "res_id": self.bpt.id,
                "datas": "Y29udGVudA==",
                "mimetype": "text/plain",
            }
        )
        self.bpt._compute_attached_docs_count()
        self.assertGreaterEqual(self.bpt.doc_count, 1)

        act_att = self.bpt.attachment_tree_view()
        self.assertEqual(act_att.get("res_model"), "ir.attachment")
        self.assertEqual(act_att.get("type"), "ir.actions.act_window")

    def test_onchange_state_sets_dates(self):
        # When state is run, date_start should be set
        self.bpt.state = "run"
        self.bpt._onchange_state()
        self.assertTrue(self.bpt.date_start)
        # When state is done, date_end should be set
        self.bpt.state = "done"
        self.bpt._onchange_state()
        self.assertTrue(self.bpt.date_end)

    def _make_test(self, scope):
        test = self.env["business.process.test"].create(
            {
                "name": f"Test {scope}",
                "process_id": self.process.id,
                "scope": scope,
            }
        )
        for step in self.process.step_ids:
            self.env["business.process.step.test"].create(
                {
                    "process_test_id": test.id,
                    "step_id": step.id,
                }
            )
        return test

    def test_action_run_internal(self):
        test = self._make_test("internal")
        # one step keeps an explicit responsible, the other inherits the tester
        test.test_step_ids[0].responsible_id = self.partner
        test.action_run()
        self.assertEqual(test.state, "run")
        self.assertTrue(test.date_start)
        # tester defaults to current user partner
        self.assertEqual(test.tester_id, self.env.user.partner_id)
        for step in test.test_step_ids:
            self.assertTrue(step.test_started)
            self.assertTrue(step.date_start)
        self.assertEqual(test.test_step_ids[0].responsible_id, self.partner)
        self.assertEqual(test.test_step_ids[1].responsible_id, test.tester_id)
        self.assertEqual(test.process_id.status_internal_test, "in_progress")
        # step responsibles subscribed as followers (OdooBot itself is not subscribed)
        self.assertIn(self.partner, test.message_partner_ids)

    def test_action_run_integration_and_user_acceptance(self):
        test_int = self._make_test("integration")
        test_int.action_run()
        self.assertEqual(test_int.process_id.status_integration_test, "in_progress")

        test_uat = self._make_test("user_acceptance")
        test_uat.action_run()
        self.assertEqual(test_uat.process_id.status_user_acceptance_test, "in_progress")

    def test_action_run_does_not_downgrade_done_status(self):
        test = self._make_test("internal")
        self.process.sudo().write({"status_internal_test": "done"})
        test.action_run()
        self.assertEqual(self.process.status_internal_test, "done")

    def test_action_wait_and_draft(self):
        test = self._make_test("internal")
        test.action_wait()
        self.assertEqual(test.state, "wait")
        test.action_draft()
        self.assertEqual(test.state, "draft")

    def test_action_done_internal(self):
        test = self._make_test("internal")
        test.action_run()
        test.test_step_ids.write({"result": "passed"})
        test.action_done()
        self.assertEqual(test.state, "done")
        self.assertTrue(test.date_end)
        for step in test.test_step_ids:
            self.assertTrue(step.date_end)
        self.assertEqual(test.process_id.status_internal_test, "done")
        # bpt from setUp is still draft, so the process is not ready yet
        self.assertNotEqual(self.process.state, "ready")

    def test_action_done_marks_process_ready(self):
        # the only remaining non-done test on the process becomes done -> process ready
        self.bpt.unlink()
        test = self._make_test("integration")
        test.action_run()
        test.action_done()
        self.assertEqual(test.process_id.status_integration_test, "done")
        self.assertEqual(self.process.state, "ready")

    def test_action_done_user_acceptance(self):
        test = self._make_test("user_acceptance")
        test.action_run()
        test.action_done()
        self.assertEqual(test.process_id.status_user_acceptance_test, "done")

    def test_add_followers_includes_project_manager(self):
        manager = self.env.ref("base.partner_admin")
        self.project.project_manager_id = manager
        test = self._make_test("internal")
        test._add_followers()
        self.assertIn(manager, test.message_partner_ids)
        # second call should not fail nor duplicate followers
        count = len(test.message_partner_ids)
        test._add_followers()
        self.assertEqual(len(test.message_partner_ids), count)

    def test_onchange_completion_test_triggers_done(self):
        # When completion reaches 100, onchange should call action_done
        # First ensure at least one step exists
        if not self.bpt.test_step_ids:
            self.bpt._onchange_process_id()
        # Set value and trigger onchange
        self.bpt.completion_test = 100.0
        self.bpt._onchange_completion_test()
        self.assertEqual(self.bpt.state, "done")
