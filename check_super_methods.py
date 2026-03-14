#!/usr/bin/env python3
"""
check_super_methods - pre-commit hook pentru Odoo
==================================================
Verifică dacă metodele apelate prin super() există în clasele părinte.

Mod de utilizare ca pre-commit hook (automat primește fișierele staged):
    pre-commit run check-super-methods

Mod manual:
    python check_super_methods.py models/sale_order.py models/res_partner.py
    python check_super_methods.py models/ --addons-path /opt/odoo/addons
"""

import argparse
import ast
import logging
import os
import sys
from dataclasses import dataclass, field

# Configurare logger de bază
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
#  Structuri de date
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class SuperCall:
    class_name: str
    method_name: str
    super_method: str
    lineno: int
    col_offset: int


@dataclass
class ClassInfo:
    name: str
    bases: list
    methods: list
    super_calls: list = field(default_factory=list)
    lineno: int = 0


@dataclass
class CheckResult:
    super_call: SuperCall
    filepath: str
    status: str  # "OK" | "MISSING" | "UNKNOWN_BASE" | "BUILTIN"
    found_in: str | None = None
    message: str = ""


# ─────────────────────────────────────────────────────────────────────────────
#  Vizitator AST
# ─────────────────────────────────────────────────────────────────────────────


class SuperCallVisitor(ast.NodeVisitor):
    def __init__(self):
        self.classes: dict = {}
        self._current_class: str | None = None
        self._current_method: str | None = None

    def visit_ClassDef(self, node: ast.ClassDef):
        bases = [self._expr_to_str(b) for b in node.bases]
        self.classes[node.name] = ClassInfo(name=node.name, bases=bases, methods=[], lineno=node.lineno)
        prev = self._current_class
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = prev

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self._current_class:
            self.classes[self._current_class].methods.append(node.name)
        prev = self._current_method
        self._current_method = node.name
        self.generic_visit(node)
        self._current_method = prev

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node: ast.Call):
        if (
            self._current_class
            and self._current_method
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Call)
            and self._is_super(node.func.value)
        ):
            self.classes[self._current_class].super_calls.append(
                SuperCall(
                    class_name=self._current_class,
                    method_name=self._current_method,
                    super_method=node.func.attr,
                    lineno=node.lineno,
                    col_offset=node.col_offset,
                )
            )
        self.generic_visit(node)

    @staticmethod
    def _is_super(node: ast.Call) -> bool:
        return isinstance(node.func, ast.Name) and node.func.id == "super"

    @staticmethod
    def _expr_to_str(expr) -> str:
        if isinstance(expr, ast.Name):
            return expr.id
        if isinstance(expr, ast.Attribute):
            return f"{SuperCallVisitor._expr_to_str(expr.value)}.{expr.attr}"
        return "<unknown>"


# ─────────────────────────────────────────────────────────────────────────────
#  Registru global (addons-path opțional)
# ─────────────────────────────────────────────────────────────────────────────


def build_global_registry(addons_path: str) -> dict:
    registry = {}
    for root, dirs, files in os.walk(addons_path):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules", ".venv", "venv", "static"}]
        for fn in files:
            if not fn.endswith(".py"):
                continue
            fp = os.path.join(root, fn)
            try:
                with open(fp, encoding="utf-8", errors="ignore") as fh:
                    src = fh.read()
                v = SuperCallVisitor()
                v.visit(ast.parse(src, filename=fp))
                for name, info in v.classes.items():
                    if name not in registry:
                        registry[name] = info
                    else:
                        registry[name].methods = list(set(registry[name].methods + info.methods))
            except Exception as e:
                logger.debug("Eroare la procesarea fisierului %s: %s", fp, e)
    return registry


# ─────────────────────────────────────────────────────────────────────────────
#  Rezolvare metode în ierarhia de baze
# ─────────────────────────────────────────────────────────────────────────────

BUILTIN_METHODS = {
    # Python dunder
    "__init__",
    "__new__",
    "__str__",
    "__repr__",
    "__eq__",
    "__hash__",
    "__lt__",
    "__le__",
    "__gt__",
    "__ge__",
    "__bool__",
    "__len__",
    "__getitem__",
    "__setitem__",
    "__delitem__",
    "__contains__",
    "__iter__",
    "__next__",
    "__enter__",
    "__exit__",
    "__getattr__",
    "__setattr__",
    "__delattr__",
    "__call__",
    # Odoo ORM standard
    "create",
    "write",
    "unlink",
    "read",
    "search",
    "browse",
    "copy",
    "name_get",
    "name_search",
    "fields_get",
    "fields_view_get",
    "default_get",
    "onchange",
    "load",
    "export_data",
    "action_confirm",
    "action_cancel",
    "action_draft",
    "action_done",
    "_compute_display_name",
    "_search",
    "_read_group",
}

KNOWN_ODOO_BASES = {
    "Model",
    "TransientModel",
    "AbstractModel",
    "models.Model",
    "models.TransientModel",
    "models.AbstractModel",
    "BaseModel",
    "object",
}


def resolve(method: str, bases: list, local: dict, registry: dict, _visited: set | None = None) -> tuple:
    if _visited is None:
        _visited = set()

    if method in BUILTIN_METHODS:
        return "BUILTIN", None

    for base in bases:
        if base in _visited:
            continue
        _visited.add(base)

        if base in KNOWN_ODOO_BASES:
            return "OK", base

        info = local.get(base) or registry.get(base)
        if info is None:
            return "UNKNOWN_BASE", base

        if method in info.methods:
            return "OK", base

        status, found = resolve(method, info.bases, local, registry, _visited)
        if status in ("OK", "BUILTIN"):
            return status, found

    return "MISSING", None


# ─────────────────────────────────────────────────────────────────────────────
#  Verificare fișier
# ─────────────────────────────────────────────────────────────────────────────


def check_file(filepath: str, registry: dict) -> list:
    try:
        with open(filepath, encoding="utf-8") as fh:
            src = fh.read()
    except OSError as e:
        logger.error("  [EROARE] Nu pot citi '%s': %s", filepath, e)
        return []

    try:
        tree = ast.parse(src, filename=filepath)
    except SyntaxError as e:
        logger.error("  [EROARE] Sintaxă invalidă în '%s': %s", filepath, e)
        return []

    visitor = SuperCallVisitor()
    visitor.visit(tree)

    results = []
    for _cls_name, cls_info in visitor.classes.items():
        for sc in cls_info.super_calls:
            status, found_in = resolve(sc.super_method, cls_info.bases, visitor.classes, registry)
            if status == "OK":
                msg = f"găsit în '{found_in}'"
            elif status == "BUILTIN":
                msg = "metodă built-in / Odoo ORM standard"
            elif status == "UNKNOWN_BASE":
                msg = (
                    f"clasa de bază '{found_in}' nu a putut fi rezolvată "
                    f"(import extern sau lipsă din --addons-path)"
                )
            else:
                msg = f"'{sc.super_method}' NU există în nicio bază: " f"{cls_info.bases}"
            results.append(
                CheckResult(
                    super_call=sc,
                    filepath=filepath,
                    status=status,
                    found_in=found_in,
                    message=msg,
                )
            )
    return results


# ─────────────────────────────────────────────────────────────────────────────
#  Colectare fișiere
# ─────────────────────────────────────────────────────────────────────────────


def collect_python_files(paths: list) -> list:
    files = []
    for p in paths:
        if os.path.isfile(p):
            if p.endswith(".py"):
                files.append(p)
        elif os.path.isdir(p):
            for root, dirs, fns in os.walk(p):
                dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules", ".venv", "venv"}]
                for fn in fns:
                    if fn.endswith(".py"):
                        files.append(os.path.join(root, fn))
    return files


# ─────────────────────────────────────────────────────────────────────────────
#  Raport (scris pe stderr — standard pre-commit)
# ─────────────────────────────────────────────────────────────────────────────

USE_COLOR = sys.stderr.isatty()

_C = {
    "R": "\033[91m",
    "G": "\033[92m",
    "Y": "\033[93m",
    "C": "\033[96m",
    "B": "\033[1m",
    "D": "\033[2m",
    "X": "\033[0m",
}


def _c(key: str, text: str) -> str:
    return (_C.get(key, "") + text + _C["X"]) if USE_COLOR else text


def print_report(all_results: list, files_checked: int) -> int:
    missing = [r for r in all_results if r.status == "MISSING"]
    unknown = [r for r in all_results if r.status == "UNKNOWN_BASE"]
    ok_total = [r for r in all_results if r.status in ("OK", "BUILTIN")]

    # Se folosește sys.stderr pentru raport pentru a nu interfera cu output-ul pre-commit
    sys.stderr.write("\n")
    sys.stderr.write(_c("B", "  check-super-methods") + "\n")
    sys.stderr.write(_c("D", f"  {files_checked} fișier(e) · {len(all_results)} apel(uri) super()") + "\n")

    if missing:
        sys.stderr.write("\n")
        sys.stderr.write(_c("R", f"  ✘ METODE LIPSĂ ({len(missing)})") + "\n")
        for r in missing:
            sc = r.super_call
            sys.stderr.write(
                f"    {_c('D', f'{r.filepath}:{sc.lineno}:{sc.col_offset}')}  "
                f"{_c('C', sc.class_name)}.{_c('B', sc.super_method)}  "
                f"{_c('D', f'(în {sc.method_name!r})')}\n"
            )
            sys.stderr.write(_c("R", f"      → {r.message}") + "\n")

    if unknown:
        sys.stderr.write("\n")
        sys.stderr.write(_c("Y", f"  ⚠ BAZE NECUNOSCUTE ({len(unknown)}) — neputând fi verificate") + "\n")
        for r in unknown:
            sc = r.super_call
            sys.stderr.write(
                f"    {_c('D', f'{r.filepath}:{sc.lineno}:{sc.col_offset}')}  "
                f"{_c('C', sc.class_name)}.{_c('B', sc.super_method)}\n"
            )
            sys.stderr.write(_c("Y", f"      → {r.message}") + "\n")

    sys.stderr.write("\n")
    if missing:
        sys.stderr.write(_c("R", f"  EȘUAT — {len(missing)} metodă/metode lipsă") + "\n\n")
        return 1

    suffix = f"  ⚠ {len(unknown)} baze necunoscute (folosiți --addons-path)" if unknown else ""
    sys.stderr.write(_c("G", f"  ✔ OK — {len(ok_total)} apel(uri) super() verificate{suffix}") + "\n\n")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
#  Entry-point
# ─────────────────────────────────────────────────────────────────────────────


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="pre-commit hook: verifică metodele super() în fișiere Python Odoo.",
    )
    parser.add_argument(
        "filenames",
        nargs="*",
        metavar="FILE",
        help="Fișiere/directoare Python (furnizate automat de pre-commit).",
    )
    parser.add_argument(
        "--addons-path",
        metavar="PATH",
        default=os.environ.get("ODOO_ADDONS_PATH", ""),
        help=(
            "Calea addons Odoo pentru rezolvarea claselor de bază. "
            "Poate fi setat și prin variabila ODOO_ADDONS_PATH."
        ),
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Dezactivează culorile ANSI.",
    )

    args = parser.parse_args(argv)

    global USE_COLOR
    if args.no_color:
        USE_COLOR = False

    files = collect_python_files(args.filenames or ["."])
    if not files:
        sys.stderr.write("  [check-super-methods] Niciun fișier .py de verificat.\n")
        return 0

    registry = {}
    if args.addons_path and os.path.isdir(args.addons_path):
        sys.stderr.write(_c("D", f"  [check-super-methods] Indexez {args.addons_path} ...") + "\n")
        registry = build_global_registry(args.addons_path)

    all_results = []
    for fp in files:
        all_results.extend(check_file(fp, registry))

    return print_report(all_results, len(files))


if __name__ == "__main__":
    sys.exit(main())
