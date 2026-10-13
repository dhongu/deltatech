# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
from odoo.tests import TransactionCase, tagged

from ..hooks import DONORS, FIELD_NAMES, _moved_xml_ids


@tagged("post_install", "-at_install")
class TestEcrFiscalMixin(TransactionCase):
    def _models_under_test(self):
        """Modelele pe care contractul chiar se aplică în baza curentă.

        `account.move` vine din dependența proprie, deci e mereu acolo. `pos.order`
        apare doar dacă `deltatech_pos` e instalat: acest modul nu mai depinde de
        `point_of_sale`, tocmai ca alternativa fără POS (`deltatech_sale_store`) să nu
        îl mai tragă. Fără filtrul ăsta, testele ar cădea pe orice bază fără POS.
        """
        return [model for model in ("pos.order", "account.move") if model in self.env]

    def test_fields_present_on_both_models(self):
        """Contractul trebuie să existe pe fiecare model pe care e aplicat."""
        for model in self._models_under_test():
            fields = self.env[model]._fields
            for name in FIELD_NAMES:
                self.assertIn(name, fields, f"{name} lipsește pe {model}")

    def test_fields_are_readonly_and_not_copied(self):
        """Sunt pistă de audit: nu se editează manual și nu se duplică la copiere."""
        for model in self._models_under_test():
            for name in FIELD_NAMES:
                field = self.env[model]._fields[name]
                self.assertTrue(field.readonly, f"{model}.{name} ar trebui readonly")
                self.assertFalse(field.copy, f"{model}.{name} nu ar trebui copiat")

    def test_fields_claimed_by_this_module(self):
        """Acest modul deține o referință la fiecare câmp mutat aici.

        Dacă `pre_init_hook` n-ar prelua rândurile din `ir_model_data`, actualizarea
        modulelor donoare ar putea curăța înregistrările care nu mai sunt declarate de
        ele și ar șterge coloanele împreună cu numerele de bon fiscal.

        NU verificăm exclusivitatea: modulele donoare moștenesc mixinul, deci Odoo le
        recreează propriile rânduri pentru aceleași câmpuri. Proprietatea devine
        partajată, iar câmpul supraviețuiește dezinstalării oricăruia dintre ele —
        exact ce vrem. O aserțiune de exclusivitate ar trece pe o bază unde donoarele
        nu sunt instalate și ar cădea în producție, unde sunt.
        """
        for model in self._models_under_test() + ["account.bank.statement.line"]:
            for xml_id in _moved_xml_ids(model):
                data = self.env["ir.model.data"].search([("name", "=", xml_id), ("model", "=", "ir.model.fields")])
                self.assertTrue(data, f"{xml_id} nu există")
                self.assertIn(
                    "deltatech_ecr_fiscal",
                    data.mapped("module"),
                    f"{xml_id} nu e revendicat de deltatech_ecr_fiscal",
                )

    def test_moved_xml_ids_shape(self):
        self.assertEqual(
            _moved_xml_ids("pos.order")[0],
            "field_pos_order__fiscal_receipt_number",
        )
        models = {m for models in DONORS.values() for m in models}
        # Linia de extras delegă către factură: câmpurile ei delegate trebuie și ele
        # preluate, altfel rămân pe modulul donor și sunt curățate la actualizarea lui.
        self.assertEqual(models, {"pos.order", "account.move", "account.bank.statement.line"})
