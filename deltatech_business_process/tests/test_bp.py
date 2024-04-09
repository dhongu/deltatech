# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestBusinessProcess(TransactionCase):
    def setUp(self):
        super().setUp()
        self.area = self.env["business.area"].create(
            {
                "name": "Test Business Area",
            }
        )
        self.project = self.env["business.project"].create(
            {
                "name": "Test Project",
            }
        )
        self.process = self.env["business.process"].create(
            {
                "name": "Test Process",
                "area_id": self.area.id,
                "project_id": self.project.id,
                "code": "TEST1",
                "step_ids": [
                    (0, 0, {"name": "Test Step 1"}),
                    (0, 0, {"name": "Test Step 2"}),
                ],
            }
        )

    def test_project(self):
        """Test creation of a project"""
        project = self.project
        project.action_view_processes()
        project.action_view_issue()
        project.action_view_step()
        project.action_view_developments()

    def test_create_business_process(self):
        """Test creation of a business process"""
        business_process = Form(self.env["business.process"])
        business_process.code = "CODE1"
        business_process.name = "Test Business Process"
        business_process.area_id = self.area
        business_process.project_id = self.project

        with business_process.step_ids.new() as step:
            step.name = "Test Step 1"
        with business_process.step_ids.new() as step:
            step.name = "Test Step 2"

        business_process = business_process.save()

        self.env["business.process"]._name_search("CODE1")

        business_process.button_start_design()
        business_process.button_start_test()
        business_process.button_end_test()

        export_form = Form(self.env["business.process.export"].with_context(active_ids=[business_process.id]))
        export_form = export_form.save()
        export_form.do_export()
        export_form.do_back()

        import_form = Form(self.env["business.process.import"].with_context(active_ids=[self.project.id]))
        import_form.data_file = export_form.data_file
        import_form = import_form.save()
        import_form.do_import()
        import_form.do_back()

    def test_create_business_process_test(self):
        business_process_test = Form(self.env["business.process.test"])
        business_process_test.process_id = self.process
        business_process_test = business_process_test.save()
        business_process_test.action_run()

        business_process_test.action_view_test_steps()
        business_process_test.attachment_tree_view()
        business_process_test.action_done()
        test_step_ids = business_process_test.test_step_ids
        test_step_ids[0].result = "passed"
        test_step_ids[1].result = "failed"
        test_step_ids[1].action_view_issue()

    def test_creare_issue(self):
        """Test creation of an issue"""
        issue = Form(self.env["business.issue"])
        issue.name = "Test Issue"
        issue.area_id = self.area
        issue.customer_id = self.project.customer_id
        issue.project_id = self.project
        issue.process_id = self.process
        issue = issue.save()

        issue.button_in_progress()

        issue.button_in_test()
        issue.solution_date = fields.Date.today()
        issue.solution = "Test Solution"
        issue.button_solved()
        issue.button_draft()
        issue.closed_date = fields.Date.today()
        issue.button_done()

    # def test_migration(self):
    #     """Test creation of a migration"""
    #     migration = Form(self.env['business.migration'])
    #     migration.name = 'Test Migration'
    #     migration.area_id = self.area
    #     migration.project_id = self.project
    #     migration = migration.save()
    #
    #     migration_test = Form(self.env['business.migration.test'])
    #     migration_test.name = 'Test Migration Test'
    #     migration_test.migration_id = migration
    #     migration_test = migration_test.save()
    #     migration_test.action_run()
