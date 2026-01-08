from odoo.tests.common import TransactionCase


class TestAccessCredentials(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a access credentials
        self.credentials = self.env["access.credentials"].create(
            {
                "name": "Test Credentials",
                "code": "test_code",
                "access_type": "user",
                "username": "test_user",
                "password": "test_password",
            }
        )

    def test_check_credentials(self):
        # Check if the credentials are correctly set
        self.assertEqual(self.credentials.name, "Test Credentials", "Name is not correctly set")
        self.assertEqual(self.credentials.code, "test_code", "Code is not correctly set")
        self.assertEqual(self.credentials.access_type, "user", "Access type is not correctly set")
        self.assertEqual(self.credentials.username, "test_user", "Username is not correctly set")
        self.assertEqual(self.credentials.password, "test_password", "Password is not correctly set")

    def test_change_credentials(self):
        # Change the credentials
        self.credentials.write(
            {
                "name": "Changed Credentials",
                "code": "changed_code",
                "access_type": "client",
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
            }
        )

        # Check if the credentials are correctly updated
        self.assertEqual(self.credentials.name, "Changed Credentials", "Name is not correctly updated")
        self.assertEqual(self.credentials.code, "changed_code", "Code is not correctly updated")
        self.assertEqual(self.credentials.access_type, "client", "Access type is not correctly updated")
        self.assertEqual(self.credentials.client_id, "test_client_id", "Client ID is not correctly updated")
        self.assertEqual(self.credentials.client_secret, "test_client_secret", "Client Secret is not correctly updated")
