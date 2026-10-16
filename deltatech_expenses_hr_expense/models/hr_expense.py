# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HrExpense(models.Model):
    _inherit = "hr.expense"

    expenses_deduction_id = fields.Many2one(
        "deltatech.expenses.deduction",
        string="Expenses Deduction",
        copy=False,
        readonly=True,
        index="btree_not_null",
        help="Dacă este completat, cheltuiala este decontată prin acest Decont de cheltuieli "
        "(deltatech_expenses), iar notele contabile NU se generează din modulul standard, "
        "pentru a evita dublarea cheltuielilor.",
    )

    def _create_move(self):
        """Nu generăm note contabile din modulul standard pentru cheltuielile preluate
        într-un Decont de cheltuieli — acolo se face contabilizarea. În Odoo 20 nota se creează
        la aprobare (`_do_approve`), nu mai există butonul separat de postare."""
        linked = self.filtered("expenses_deduction_id")
        if linked:
            _logger.info(
                "deltatech_expenses: %s cheltuieli sunt decontate prin Decont; "
                "nota contabilă standard este sărită pentru a evita dublarea.",
                len(linked),
            )
        to_move = self - linked
        if to_move:
            return super(HrExpense, to_move)._create_move()
        return False
