# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com>
# License LGPL-3 (see module manifest)

from odoo.tests import Form
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProjectPricelist(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env["res.partner"]
        cls.Project = cls.env["project.project"]
        cls.SaleOrder = cls.env["sale.order"]
        cls.Pricelist = cls.env["product.pricelist"]
        cls.Task = cls.env["project.task"]

        # Basic partner
        cls.partner = cls.Partner.create(
            {
                "name": "Test Customer",
                "email": "customer@example.com",
            }
        )

        # Two simple pricelists (no items needed for these tests)
        usd = cls.env.ref("base.USD")
        eur = cls.env.ref("base.EUR")
        cls.pricelist_a = cls.Pricelist.create(
            {
                "name": "PL A",
                "currency_id": usd.id,
            }
        )
        cls.pricelist_b = cls.Pricelist.create(
            {
                "name": "PL B",
                "currency_id": eur.id,
            }
        )

        # Project with project-level pricelist A set
        cls.project = cls.Project.create(
            {
                "name": "Priced Project",
                "pricelist_id": cls.pricelist_a.id,
            }
        )

        # A simple task in the project
        cls.task = cls.Task.create(
            {
                "name": "Task A",
                "project_id": cls.project.id,
            }
        )

    def test_action_view_sos_injects_default_pricelist(self):
        action = self.project.action_view_sos()
        ctx = action.get("context", {})
        self.assertEqual(
            ctx.get("default_pricelist_id"),
            self.project.pricelist_id.id,
            "Project Sales Orders action should inject default_pricelist_id from project.",
        )

    def test_so_create_uses_pricelist_with_create_for_project_ctx(self):
        so = self.SaleOrder.with_context(create_for_project_id=self.project.id).create(
            {
                "partner_id": self.partner.id,
            }
        )
        self.assertEqual(
            so.pricelist_id,
            self.project.pricelist_id,
            "SO created with create_for_project_id should use project's pricelist.",
        )

    def test_so_create_uses_pricelist_with_default_project_ctx(self):
        so = self.SaleOrder.with_context(default_project_id=self.project.id).create(
            {
                "partner_id": self.partner.id,
            }
        )
        self.assertEqual(
            so.pricelist_id,
            self.project.pricelist_id,
            "SO created with default_project_id should use project's pricelist.",
        )

    def test_so_create_uses_pricelist_with_project_in_vals(self):
        so = self.SaleOrder.create(
            {
                "partner_id": self.partner.id,
                "project_id": self.project.id,
            }
        )
        self.assertEqual(
            so.pricelist_id,
            self.project.pricelist_id,
            "SO created with project_id in vals should use project's pricelist.",
        )

    def test_explicit_pricelist_not_overridden(self):
        so = self.SaleOrder.with_context(create_for_project_id=self.project.id).create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.pricelist_b.id,
            }
        )
        self.assertEqual(
            so.pricelist_id,
            self.pricelist_b,
            "Explicit pricelist on SO should not be overridden by project's pricelist.",
        )

    def test_so_create_from_task_uses_project_pricelist(self):
        so = self.SaleOrder.with_context(
            create_for_task_id=self.task.id,
            default_project_id=self.project.id,
        ).create(
            {
                "partner_id": self.partner.id,
            }
        )
        self.assertEqual(
            so.pricelist_id,
            self.project.pricelist_id,
            "SO created from task should use the task's project's pricelist.",
        )

    def test_so_create_from_task_respects_explicit_pricelist(self):
        so = self.SaleOrder.with_context(
            create_for_task_id=self.task.id,
            default_project_id=self.project.id,
        ).create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.pricelist_b.id,
            }
        )
        self.assertEqual(
            so.pricelist_id,
            self.pricelist_b,
            "SO created from task with explicit pricelist should keep it.",
        )

    def test_default_get_sets_pricelist_from_task_context(self):
        # Simulate opening the SO form from a task (before saving)
        ctx = {
            "create_for_task_id": self.task.id,
            "default_project_id": self.project.id,
            "default_partner_id": self.partner.id,
        }
        with Form(self.SaleOrder.with_context(ctx)) as so_form:
            # Pricelist should be proposed from the project's pricelist
            self.assertEqual(so_form.pricelist_id, self.project.pricelist_id)

    def test_default_get_respects_explicit_default_pricelist_in_context(self):
        # If the context provides default_pricelist_id, do not override it
        ctx = {
            "create_for_task_id": self.task.id,
            "default_project_id": self.project.id,
            "default_partner_id": self.partner.id,
            "default_pricelist_id": self.pricelist_b.id,
        }
        with Form(self.SaleOrder.with_context(ctx)) as so_form:
            self.assertEqual(so_form.pricelist_id, self.pricelist_b)
