import os

from odoo import fields, models, modules


class LineCounterWizard(models.TransientModel):
    _name = "line.counter.wizard"
    _description = "Module Line Counter Wizard"

    module_ids = fields.Many2many("ir.module.module", string="Modules", domain=[("state", "=", "installed")])
    result = fields.Html(string="Result", readonly=True)

    def action_count_lines(self):
        total_lines = 0
        result_html = '<table class="table table-sm"><thead><tr><th>Module</th><th>Lines</th></tr></thead><tbody>'

        for module in self.module_ids:
            module_path = modules.get_module_path(module.name)
            if not module_path:
                continue

            module_lines = 0
            for root, dirs, files in os.walk(module_path):
                if "tests" in dirs:
                    dirs.remove("tests")
                for file in files:
                    if file.endswith((".py", ".xml", ".js", ".css", ".scss")):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, encoding="utf-8") as f:
                                module_lines += sum(1 for line in f if line.strip())
                        except Exception:
                            continue

            result_html += f"<tr><td>{module.shortdesc} ({module.name})</td><td>{module_lines}</td></tr>"
            total_lines += module_lines

        result_html += f"</tbody><tfoot><tr><th>Total</th><th>{total_lines}</th></tr></tfoot></table>"
        self.result = result_html

        return {
            "type": "ir.actions.act_window",
            "res_model": "line.counter.wizard",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }
