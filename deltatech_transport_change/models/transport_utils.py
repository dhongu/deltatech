import ast
import os


def _recordset_to_xmlids(rs):
    if not rs:
        return []
    mapping = rs.get_external_id()
    result = []
    for rec in rs:
        xmlid = mapping.get(rec.id)
        if not xmlid:
            xmlid = f"{rec._name},{rec.id}"
        result.append(xmlid)
    return result


def map_xmlid(val):
    """Convert Odoo values to exportable string representations.
    - False/None -> ''
    - single record -> xmlid or model,id
    - multiple records -> comma-joined xmlids
    - list/tuple -> recursive mapping and join
    - others -> str(val)
    """
    if not val:
        return ""
    if hasattr(val, "ids") and hasattr(val, "env"):
        if len(val) == 1:
            return _recordset_to_xmlids(val)[0]
        else:
            return ",".join(_recordset_to_xmlids(val))
    if isinstance(val, (list, tuple)):
        return ",".join(map(map_xmlid, val))
    return str(val)


def _bump_manifest_version_inplace(manifest_path: str):
    """Increment patch version (last segment) in a manifest dict file.
    Returns (changed: bool, new_version: str or None).
    """
    if not os.path.exists(manifest_path):
        return False, None
    with open(manifest_path, encoding="utf-8") as f:
        content = f.read()
    try:
        tree = ast.parse(content)
        if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Dict):
            dict_node = tree.body[0].value
        elif tree.body and isinstance(tree.body[0], ast.Assign) and isinstance(tree.body[0].value, ast.Dict):
            dict_node = tree.body[0].value
        else:
            return False, None
        manifest_dict = ast.literal_eval(dict_node)
    except Exception:
        return False, None

    version = manifest_dict.get("version") or manifest_dict.get("Version") or manifest_dict.get("VERSION")
    if not version or not isinstance(version, str):
        return False, None
    parts = version.split(".")
    try:
        if parts:
            parts[-1] = str(int(parts[-1]) + 1)
        new_version = ".".join(parts)
    except Exception:
        return False, None
    if new_version == version:
        return False, None
    manifest_dict["version"] = new_version
    import pprint

    rendered = pprint.pformat(manifest_dict, width=120, sort_dicts=False) + "\n"
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(rendered)
    return True, new_version
