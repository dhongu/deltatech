#!/usr/bin/env python3
"""Verifică compatibilitatea licenței fiecărui modul cu licențele dependențelor sale.

Regulile sunt cele din tabelul de compatibilitate din FAQ-ul Odoo Apps
(https://apps.odoo.com/apps/faq#maintainer_faq_04). Un modul poate depinde doar de
licențele din coloana a doua; în special OPL-1 și LGPL-3 NU pot depinde de AGPL-3/GPL-3:

    AGPL-3  → AGPL-3, GPL-3, LGPL-3
    GPL-3   → GPL-3, LGPL-3
    LGPL-3  → LGPL-3, OPL-1, OEEL-1, OSI, proprietar
    OPL-1   → LGPL-3, OPL-1, OEEL-1, OSI, proprietar
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

PERMISSIVE = {"LGPL-3", "OPL-1", "OEEL-1", "Other OSI approved licence", "Other proprietary"}

ALLOWED_DEPENDENCIES = {
    "AGPL-3": {"AGPL-3", "GPL-3", "LGPL-3"},
    "GPL-3": {"GPL-3", "LGPL-3"},
    "LGPL-3": PERMISSIVE,
    "OPL-1": PERMISSIVE,
    "Other OSI approved licence": PERMISSIVE,
    "Other proprietary": PERMISSIVE,
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


# Module copyleft (AGPL-3) din afara suitelor, de care ar putea depinde modulele noastre.
# Folosite doar când suita OCA nu e clonată (CI); altfel licența se citește din manifest.
# Adăugați aici orice modul AGPL/GPL nou folosit ca dependență.
COPYLEFT_MODULES = {
    "l10n_ro_config",
    "l10n_ro_stock",
    "l10n_ro_stock_report",
    "queue_job_cron_jobrunner",
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
    licenses.update(dict.fromkeys(COPYLEFT_MODULES, "AGPL-3"))
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
            "\nVezi https://apps.odoo.com/apps/faq#maintainer_faq_04 — soluții: modulul copyleft devine "
            "OPL-1/LGPL-3, sau dependența se elimină, sau modulul trece pe AGPL-3."
        )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
