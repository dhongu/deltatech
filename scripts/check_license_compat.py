#!/usr/bin/env python3
"""Verifică compatibilitatea licenței fiecărui modul cu licențele dependențelor sale.

Regulile sunt cele din FAQ-ul Odoo Apps (https://apps.odoo.com/apps/faq#maintainer_faq_04).
Doar trei licențe restrâng dependențele; restul (LGPL-3, OPL-1, alte licențe) pot depinde
de orice:

    AGPL-3  → AGPL-3, GPL-3, LGPL-3
    GPL-3   → GPL-3, LGPL-3
    OEEL-1  → LGPL-3, OEEL-1

Licența unei dependențe se caută întâi în suită, apoi în directoarele de addons vecine
(nucleul Odoo, Enterprise, alte suite), iar la final în lista de module Enterprise de mai
jos, ca verificarea să funcționeze și în CI, unde Enterprise nu e clonat. O dependență
negăsită nicăieri e sărită, nu raportată: nu știm ce licență are.

Folosire: python3 scripts/check_license_compat.py [--addons-dir=.]
"""

import argparse
import ast
import os
import sys

ALLOWED_DEPENDENCIES = {
    "AGPL-3": {"AGPL-3", "GPL-3", "LGPL-3"},
    "GPL-3": {"GPL-3", "LGPL-3"},
    "OEEL-1": {"LGPL-3", "OEEL-1"},
}

# Module Enterprise (OEEL-1) de care depind modulele suitelor Terrabit (l10n_ro_ent,
# deltatech, bitshop*). Folosite doar când directorul Enterprise nu e disponibil (CI).
# Același fișier e copiat în fiecare suită.
ENTERPRISE_MODULES = {
    "account_accountant",
    "account_asset",
    "account_bank_statement_import",
    "account_bank_statement_import_csv",
    "account_batch_payment",
    "account_followup",
    "account_intrastat",
    "account_reports",
    "accountant",
    "ai",
    "currency_rate_live",
    "delivery_iot",
    "documents",
    "esg",
    "helpdesk",
    "helpdesk_sale",
    "hr_appraisal",
    "hr_payroll",
    "industry_fsm",
    "l10n_eu_oss_reports",
    "l10n_ro_hr_payroll",
    "l10n_ro_hr_payroll_account",
    "l10n_ro_intrastat",
    "l10n_ro_reports",
    "l10n_ro_saft",
    "mrp_workorder",
    "partner_commission",
    "planning",
    "quality_control",
    "sale_subscription",
    "sign",
    "social",
    "stock_barcode",
    "timesheet_grid",
    "web_gantt",
}


def read_manifest(path):
    with open(path, encoding="utf-8") as f:
        return ast.literal_eval(f.read())


def scan(directory):
    """{modul: licență} pentru toate modulele dintr-un director de addons."""
    result = {}
    if not os.path.isdir(directory):
        return result
    for name in os.listdir(directory):
        manifest = os.path.join(directory, name, "__manifest__.py")
        if os.path.isfile(manifest):
            try:
                result[name] = read_manifest(manifest).get("license", "LGPL-3")
            except (SyntaxError, ValueError):
                continue
    return result


def external_licenses(addons_dir):
    """Licențele modulelor din afara suitei, din directoarele vecine care există."""
    root = os.path.abspath(os.path.join(addons_dir, "..", ".."))
    candidates = [
        os.path.join(root, "odoo", "addons"),
        os.path.join(root, "odoo", "odoo", "addons"),
        os.path.join(root, "enterprise"),
    ]
    siblings = os.path.abspath(os.path.join(addons_dir, ".."))
    if os.path.isdir(siblings):
        candidates += [os.path.join(siblings, d) for d in sorted(os.listdir(siblings))]
    licenses = dict.fromkeys(ENTERPRISE_MODULES, "OEEL-1")
    own = os.path.abspath(addons_dir)
    for directory in candidates:
        if os.path.abspath(directory) != own:
            for name, lic in scan(directory).items():
                licenses.setdefault(name, lic)
    return licenses


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--addons-dir", default=".")
    args = parser.parse_args()

    own = scan(args.addons_dir)
    external = external_licenses(args.addons_dir)
    errors = []
    for module in sorted(own):
        license_ = own[module]
        allowed = ALLOWED_DEPENDENCIES.get(license_)
        if allowed is None:
            continue
        manifest = read_manifest(os.path.join(args.addons_dir, module, "__manifest__.py"))
        for dep in manifest.get("depends", []):
            dep_license = own.get(dep) or external.get(dep)
            if dep_license and dep_license not in allowed:
                errors.append(
                    f"{module}/__manifest__.py: licența {license_} nu poate depinde de "
                    f"{dep} ({dep_license}). Permise: {', '.join(sorted(allowed))}."
                )
    for error in errors:
        print(error)
    if errors:
        print(
            "\nVezi https://apps.odoo.com/apps/faq#maintainer_faq_04 — de regulă soluția e trecerea modulului pe OPL-1."
        )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
