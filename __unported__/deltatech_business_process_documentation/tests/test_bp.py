# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


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
        channel = self.env["slide.channel"].create(
            {
                "name": "Test Channel",
                "channel_type": "documentation",
                "visibility": "members",
                "enroll": "invite",
                "active": True,
                "website_published": True,
            }
        )
        self.project = self.env["business.project"].create(
            {
                "name": "Test Project",
                "auto_generate_doc": True,
                "channel_id": channel.id,
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

        business_process.description = "Test Description"

        business_process = business_process.save()

        business_process.write({"slide_id": False})

        self.project.write({"auto_generate_doc": True, "channel_id": False})
