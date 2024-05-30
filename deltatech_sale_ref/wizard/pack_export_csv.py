
from openerp import fields, models

class wizard_excel_report(models.TransientModel):
    _name = "packops.csv.wizard"
    csv_file = fields.Binary("CSV File")
    file_name = fields.Char("Filename", size=64)
