# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons rcoot folder for license details


from odoo.tests.common import TransactionCase


class TestIrAttachment(TransactionCase):
    def test_check_file(self):
        self.env["ir.attachment"].check_filestore(delete=False)
