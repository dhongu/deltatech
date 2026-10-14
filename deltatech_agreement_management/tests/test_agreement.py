# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo.exceptions import UserError
from odoo.tests import Form, new_test_user
from odoo.tests.common import TransactionCase


class TestAgreement(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_1 = self.env["res.partner"].create({"name": "Test Partner"})
        self.agreement_type = self.env["general.agreement.type"].create({"name": "Test Agreement Type"})

    def test_create_agreement(self):
        agreement = Form(self.env["general.agreement"])
        agreement.name = "Test Agreement"
        agreement.partner_id = self.partner_1
        agreement.type_id = self.agreement_type
        agreement = agreement.save()
        self.assertEqual(agreement.state, "draft")

    def test_agreement_flow(self):
        sequence = self.env["ir.sequence"].create({"name": "Agreement", "prefix": "AGR/", "padding": 3})
        self.agreement_type.sequence_id = sequence
        agreement = self.env["general.agreement"].create(
            {"partner_id": self.partner_1.id, "type_id": self.agreement_type.id}
        )
        self.assertEqual(agreement.name, "/")
        agreement.get_name()
        self.assertTrue(agreement.name.startswith("AGR/"))
        agreement.contract_open()
        self.assertEqual(agreement.state, "open")
        with self.assertRaises(UserError):
            agreement.unlink()
        with self.assertRaises(UserError):
            agreement.print_agreement()
        agreement.contract_close()
        self.assertEqual(agreement.state, "closed")
        agreement.contract_draft()
        self.assertEqual(agreement.state, "draft")

        self.assertEqual(self.partner_1.agreement_count, 1)
        partners = self.env["res.partner"].search([("agreement_count", "!=", False)])
        self.assertIn(self.partner_1, partners)
        action = self.partner_1.view_agreements()
        self.assertEqual(action["res_model"], "general.agreement")

        agreement.unlink()
        self.assertFalse(agreement.exists())

    def test_get_name_without_sequence(self):
        agreement = self.env["general.agreement"].create({"type_id": self.agreement_type.id})
        with self.assertRaises(UserError):
            agreement.get_name()

    def test_search_agreement_count_operators(self):
        partner_2 = self.env["res.partner"].create({"name": "Two agreements"})
        partner_none = self.env["res.partner"].create({"name": "No agreement"})
        self.env["general.agreement"].create(
            [
                {"partner_id": self.partner_1.id, "type_id": self.agreement_type.id},
                {"partner_id": partner_2.id, "type_id": self.agreement_type.id},
                {"partner_id": partner_2.id, "type_id": self.agreement_type.id},
            ]
        )
        Partner = self.env["res.partner"]
        partners = self.partner_1 | partner_2 | partner_none
        self.assertEqual(partners.mapped("agreement_count"), [1, 2, 0])

        def search(operator, value):
            return Partner.search([("id", "in", partners.ids), ("agreement_count", operator, value)])

        self.assertEqual(search("!=", False), self.partner_1 | partner_2)
        self.assertEqual(search("=", False), partner_none)
        self.assertEqual(search("=", 0), partner_none)
        self.assertEqual(search("=", 2), partner_2)
        self.assertEqual(search("!=", 2), self.partner_1 | partner_none)
        self.assertEqual(search(">", 1), partner_2)
        self.assertEqual(search(">=", 1), self.partner_1 | partner_2)
        self.assertEqual(search("<", 2), self.partner_1 | partner_none)
        self.assertEqual(search("<=", 0), partner_none)
        self.assertEqual(search("in", [0, 2]), partner_2 | partner_none)
        self.assertEqual(search("not in", [1]), partner_2 | partner_none)

    def test_count_and_search_follow_access_rights(self):
        self.env["general.agreement"].create({"partner_id": self.partner_1.id, "type_id": self.agreement_type.id})
        user_no_access = new_test_user(self.env, login="agr_no_access", groups="base.group_user")
        partner = self.partner_1.with_user(user_no_access)
        self.assertEqual(partner.agreement_count, 0)
        self.assertFalse(
            partner.search([("id", "=", partner.id), ("agreement_count", ">", 0)]),
            "Without access to the agreements the partner must not match the search either",
        )

    def test_multi_company_rule(self):
        company_2 = self.env["res.company"].create({"name": "Agreement Company 2"})
        agreement_2 = self.env["general.agreement"].create(
            {"partner_id": self.partner_1.id, "type_id": self.agreement_type.id, "company_id": company_2.id}
        )
        user = new_test_user(
            self.env,
            login="agr_user_company_1",
            groups="deltatech_agreement_management.group_agreement_user",
            company_id=self.env.company.id,
            company_ids=[(6, 0, self.env.company.ids)],
        )
        Agreement = self.env["general.agreement"].with_user(user)
        self.assertNotIn(agreement_2, Agreement.search([]))
        self.assertEqual(self.partner_1.with_user(user).agreement_count, 0)
        self.partner_1.invalidate_recordset(["agreement_count"])
        both_companies = self.partner_1.with_context(allowed_company_ids=[self.env.company.id, company_2.id])
        self.assertEqual(both_companies.agreement_count, 1)

    def test_check_company(self):
        company_2 = self.env["res.company"].create({"name": "Agreement Company 2"})
        partner_company_2 = self.env["res.partner"].create({"name": "Partner company 2", "company_id": company_2.id})
        with self.assertRaises(UserError):
            self.env["general.agreement"].create(
                {"partner_id": partner_company_2.id, "type_id": self.agreement_type.id}
            )

    def test_groups_have_privilege(self):
        privilege = self.env.ref("deltatech_agreement_management.privilege_agreement")
        self.assertEqual(self.env.ref("deltatech_agreement_management.group_agreement_user").privilege_id, privilege)
        self.assertEqual(self.env.ref("deltatech_agreement_management.group_agreement_manager").privilege_id, privilege)

    def test_form_statusbar_and_type_views(self):
        arch = self.env["general.agreement"].get_view(view_type="form")["arch"]
        self.assertIn('statusbar_visible="draft,open,closed"', arch)
        views = {
            "list": "deltatech_agreement_management.view_general_agreement_type_tree",
            "form": "deltatech_agreement_management.view_general_agreement_type_form",
        }
        for view_type, xmlid in views.items():
            view = self.env["general.agreement.type"].get_view(view_type=view_type)
            self.assertEqual(view["id"], self.env.ref(xmlid).id)
