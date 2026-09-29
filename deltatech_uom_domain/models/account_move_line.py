# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, models


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = ["account.move.line", "deltatech.uom.domain.mixin"]

    @api.depends("move_id.move_type")
    def _compute_allowed_uom_ids(self):
        """EXTENDS 'account' - largeste domeniul doar pe documentele de achizitie.

        Factura de achizitie preia UM de pe comanda (`_prepare_account_move_line`) sau
        de pe linia de furnizor (`_compute_product_uom_id`), dar domeniul ei nativ nu
        contine decat `product.uom_id | product.uom_ids`. Fara extinderea asta, valoarea
        ajunge in afara propriului domeniu: se afiseaza, dar nu mai poate fi reselectata.

        Pe facturile de vanzare domeniul ramane cel standard, deliberat. Ele se trimit la
        ANAF prin e-Factura, iar `uom.uom._get_unece_code()` cade pe 'C62' ("one/piece")
        pentru orice unitate fara cod UNECE mapat. O factura emisa in "10 buc" ar declara
        cantitatea 2 cu unitatea "bucata" - valoric corect, cantitativ fals. Acelasi cod
        e folosit si de e-Transport pentru `codUnitateMasura`.
        """
        res = super()._compute_allowed_uom_ids()
        self.filtered(lambda line: line.move_id.is_purchase_document())._extend_allowed_uom_ids()
        return res
