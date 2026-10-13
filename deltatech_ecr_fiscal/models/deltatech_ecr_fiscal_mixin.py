# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class DeltatechEcrFiscalMixin(models.AbstractModel):
    """Rezultatul tipăririi pe o casă de marcat fiscală (AMEF).

    Câmpurile sunt scrise de driver — POS-ul sau butonul de tipărire din magazin,
    după răspunsul agentului Terrabit Connect — și citite de restul stivei:
    rapoarte, module de conformitate, localizarea românească.

    Contractul stă aici, într-un modul care depinde doar de module core, ca să poată
    fi consumat și din suite care nu au acces la modulele de casă de marcat.
    """

    _name = "deltatech.ecr.fiscal.mixin"
    _description = "ECR Fiscal Audit Fields"

    # Aparatul întoarce două numere: BF, numărul bonului în cadrul raportului Z, care
    # se reia la fiecare Z, și NR, numărul documentului fiscal, unic pe aparat. Cine
    # trebuie să identifice documentul fără ambiguitate folosește NR.
    fiscal_receipt_number = fields.Char(string="Fiscal receipt (BF)", readonly=True, copy=False)
    fiscal_doc_number = fields.Char(string="Fiscal document (NR)", readonly=True, copy=False)
    fiscal_z = fields.Char(string="Z report", readonly=True, copy=False)
    fiscal_state = fields.Char(string="Fiscal state", readonly=True, copy=False)
    fiscal_error = fields.Char(string="Fiscal error", readonly=True, copy=False)
