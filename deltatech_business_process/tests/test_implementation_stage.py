# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestImplementationStage(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Stage = self.env["business.process.implementation.stage"]
        self.partner = self.env["res.partner"].search([], limit=1) or self.env["res.partner"].create({"name": "Tester"})
        self.area = self.env["business.area"].create({"name": "ERP", "responsible_id": self.partner.id})
        self.project = self.env["business.project"].create(
            {"name": "Implementation", "customer_id": self.partner.id, "project_type": "remote"}
        )
        self.process = self.env["business.process"].create(
            {
                "name": "Order to Cash",
                "area_id": self.area.id,
                "project_id": self.project.id,
                "responsible_id": self.partner.id,
                "customer_id": self.partner.id,
            }
        )

    def test_default_stages_created(self):
        """The three former selection values exist as default stage records."""
        for xmlid, name in (
            ("deltatech_business_process.implementation_stage_first", "First stage"),
            ("deltatech_business_process.implementation_stage_second", "Second stage"),
            ("deltatech_business_process.implementation_stage_start", "Start"),
        ):
            stage = self.env.ref(xmlid)
            self.assertEqual(stage.name, name)

    def test_field_is_many2one(self):
        """implementation_stage_id is a Many2one to the new stage model."""
        field = self.env["business.process"]._fields["implementation_stage_id"]
        self.assertEqual(field.type, "many2one")
        self.assertEqual(field.comodel_name, "business.process.implementation.stage")

    def test_assign_default_and_custom_stage(self):
        """A process can use a default stage and a user-created custom stage."""
        first = self.env.ref("deltatech_business_process.implementation_stage_first")
        self.process.implementation_stage_id = first
        self.assertEqual(self.process.implementation_stage_id, first)

        custom = self.Stage.create({"name": "UAT sign-off", "sequence": 40})
        self.process.implementation_stage_id = custom
        self.assertEqual(self.process.implementation_stage_id.name, "UAT sign-off")

    def test_stage_ordering(self):
        """Stages are ordered by sequence."""
        names = self.Stage.search([]).mapped("name")
        self.assertEqual(names[:3], ["First stage", "Second stage", "Start"])

    def test_export_import_round_trip(self):
        """Exporting then importing preserves the stage by name and recreates
        a stage that does not yet exist (covers the get-or-create helper)."""
        importer = self.env["business.process.import"]

        # Existing default stage resolves by its human-readable name.
        self.assertEqual(
            importer._get_implementation_stage("First stage"),
            self.env.ref("deltatech_business_process.implementation_stage_first").id,
        )
        # Legacy selection key still maps to the right stage.
        self.assertEqual(
            importer._get_implementation_stage("start"),
            self.env.ref("deltatech_business_process.implementation_stage_start").id,
        )
        # Unknown value is created on the fly.
        new_id = importer._get_implementation_stage("Brand new stage")
        self.assertTrue(new_id)
        self.assertEqual(self.Stage.browse(new_id).name, "Brand new stage")
        # Empty value yields no stage.
        self.assertFalse(importer._get_implementation_stage(False))
