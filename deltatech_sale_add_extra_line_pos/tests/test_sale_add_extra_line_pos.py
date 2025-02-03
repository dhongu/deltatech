from odoo.tests.common import TransactionCase


class TestPosSession(TransactionCase):

    def setUp(self):
        super().setUp()
        # Set up demo data for testing
        self.product_model = self.env["product.product"]
        self.pos_session_model = self.env["pos.session"]
        self.pos_config_model = self.env["pos.config"]

        # Create a sample POS config
        self.pos_config = self.pos_config_model.create(
            {
                "name": "Test POS Config",
                "company_id": self.env.user.company_id.id,
                "journal_id": self.env["account.journal"]
                .search([("type", "=", "cash"), ("company_id", "=", self.env.user.company_id.id)], limit=1)
                .id,
            }
        )

        # Create a sample product with the 'extra_product_id' field set
        self.product = self.product_model.create(
            {
                "name": "Test Product",
                "extra_product_id": self.env["product.product"].create({"name": "Extra Product"}).id,
            }
        )

    def test_loader_params_product_product(self):
        # Create a new POS session
        pos_session = self.pos_session_model.create(
            {
                "name": "Test POS Session",
                "config_id": self.pos_config.id,
            }
        )

        # Get the loader parameters for product.product
        loader_params = pos_session._loader_params_product_product()

        # Check if the 'extra_product_id' field is included in the loader parameters
        self.assertIn(
            "extra_product_id",
            loader_params["search_params"]["fields"],
            "The 'extra_product_id' field should be included in the loader parameters",
        )
