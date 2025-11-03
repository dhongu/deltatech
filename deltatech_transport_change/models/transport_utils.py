import ast
import base64
import os
import stat
import tempfile
from urllib.parse import quote, urlsplit, urlunsplit

try:
    import git  # GitPython
except Exception:  # pragma: no cover
    git = None


def _recordset_to_xmlids(rs):
    if not rs:
        return []
    # get_external_id returns a dict {id: xmlid or False}
    mapping = rs.get_external_id()
    result = []
    for rec in rs:
        xmlid = mapping.get(rec.id)
        if not xmlid:
            # fallback to model,id so import scripts pot rezolva
            xmlid = f"{rec._name},{rec.id}"
        result.append(xmlid)
    return result


def map_xmlid(val):
    """Mapează valori Odoo la reprezentări exportabile.
    - False/None -> ''
    - Recordset 1 -> xmlid sau model,id
    - Recordset n -> xmlid-uri join cu virgule
    - List/Tuple -> aplică recursiv și join cu virgule
    - Alt tip -> str(val)
    """
    if not val:
        return ""
    # Odoo recordset: are .ids și .env
    if hasattr(val, "ids") and hasattr(val, "env"):
        if len(val) == 1:
            return _recordset_to_xmlids(val)[0]
        else:
            return ",".join(_recordset_to_xmlids(val))
    if isinstance(val, (list, tuple)):
        return ",".join(map(map_xmlid, val))
    return str(val)


def write_to_module_data_folder(data_content: str, module_name: str, filename: str):
    """Writes content into the module's data/ folder, ensuring the path is safe.
    Returns tuple (abs_path, rel_manifest_path).
    """
    from odoo.modules.module import get_module_path

    # sanitize filename: no directory traversal
    sanitized = filename.strip().lstrip("/").replace("\\", "/")
    parts = [p for p in sanitized.split("/") if p not in ("", ".", "..")]
    if not parts:
        raise Exception("Invalid export filename.")
    rel_manifest_path = os.path.join("data", *parts)

    module_path = get_module_path(module_name)
    abs_path = os.path.join(module_path, rel_manifest_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8", newline="") as f:
        f.write(data_content)
    return abs_path, rel_manifest_path


def ensure_manifest_has_data(module_name: str, rel_manifest_path: str):
    """Ensure that __manifest__.py of the module contains rel_manifest_path in its 'data' list.
    Returns absolute path to manifest and a boolean indicating whether a change was applied.
    """
    from odoo.modules.module import get_module_path

    module_path = get_module_path(module_name)
    manifest_path = os.path.join(module_path, "__manifest__.py")
    if not os.path.exists(manifest_path):
        raise Exception(f"__manifest__.py nu a fost găsit în modulul {module_name}.")

    with open(manifest_path, encoding="utf-8") as f:
        content = f.read()

    tree = ast.parse(content)
    # The manifest is typically a single dict literal expression
    dict_node = None
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Dict):
        dict_node = tree.body[0].value
    elif tree.body and isinstance(tree.body[0], ast.Assign) and isinstance(tree.body[0].value, ast.Dict):
        dict_node = tree.body[0].value
    if dict_node is None:
        raise Exception("Structura __manifest__.py nu a putut fi analizată ca dict.")

    manifest_dict = ast.literal_eval(dict_node)
    data_list = manifest_dict.get("data")
    if data_list is None:
        data_list = []
    if rel_manifest_path not in data_list:
        data_list.append(rel_manifest_path)
        manifest_dict["data"] = data_list
        # Re-render manifest
        import pprint

        rendered = pprint.pformat(manifest_dict, width=120, sort_dicts=False)
        # Ensure trailing newline
        rendered = rendered + "\n"
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(rendered)
        return manifest_path, True
    return manifest_path, False


def _push_with_ssh_key(g, remote, branch, ssh_key_b64: bytes):
    # scriem cheia într-un fișier temporar cu permisiuni 0600
    key_fd, key_path = tempfile.mkstemp(prefix="odoo_git_", suffix=".key")
    try:
        os.write(key_fd, base64.b64decode(ssh_key_b64))
        os.close(key_fd)
        os.chmod(key_path, stat.S_IRUSR | stat.S_IWUSR)
        # folosim GIT_SSH_COMMAND doar pe durata push-ului
        with g.git.custom_environment(GIT_SSH_COMMAND=f"ssh -i {key_path} -o StrictHostKeyChecking=no"):
            remote.push(refspec=f"HEAD:{branch}")
    finally:
        try:
            os.remove(key_path)
        except Exception:
            pass


def _push_with_https(g, remote, branch, username: str, password: str):
    # Inserăm credentialele în URL doar temporar
    urls = list(remote.urls)
    if not urls:
        remote.push(refspec=f"HEAD:{branch}")
        return
    original_url = urls[0]
    split = urlsplit(original_url)
    if split.scheme not in ("http", "https"):
        # dacă nu e https, fallback la push normal
        remote.push(refspec=f"HEAD:{branch}")
        return
    safe_user = quote(username, safe="")
    safe_pass = quote(password, safe="")
    netloc = split.hostname or ""
    if split.port:
        netloc = f"{netloc}:{split.port}"
    auth_netloc = f"{safe_user}:{safe_pass}@{netloc}"
    temp_url = urlunsplit((split.scheme, auth_netloc, split.path, split.query, split.fragment))
    try:
        remote.set_url(temp_url)
        remote.push(refspec=f"HEAD:{branch}")
    finally:
        # revenim la URL-ul original
        remote.set_url(original_url)


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
    # render back
    import pprint

    rendered = pprint.pformat(manifest_dict, width=120, sort_dicts=False) + "\n"
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(rendered)
    return True, new_version


def git_commit_push(file_path, message, repo):
    """Use GitPython to add/commit/push if changes exist.
    Utilizează credențialele din `transport.repo` dacă sunt setate.
    Acceptă fie o cale de fișier (str), fie o listă/tuplu de căi.
    În plus: include automat și `__manifest__.py` al modulului țintă și îi incrementează versiunea înainte de commit.
    """
    if git is None:
        # GitPython nu este instalat
        raise Exception("GitPython (package 'git') nu este instalat. Instalează-l pentru a folosi integrarea Git.")

    # Normalize to list
    if isinstance(file_path, (list, tuple)):
        file_paths = list(file_path)
    else:
        file_paths = [file_path]

    if not file_paths:
        return

    # Determinăm manifestul modulului țintă și îl includem
    manifest_path = None
    try:
        from odoo.modules.module import get_module_path

        if getattr(repo, "module_name", False):
            module_path = get_module_path(repo.module_name)
            manifest_path = os.path.join(module_path, "__manifest__.py")
            # bump version înainte de stage
            changed, _ = _bump_manifest_version_inplace(manifest_path)
            if manifest_path not in file_paths:
                file_paths.append(manifest_path)
    except Exception:
        # dacă nu putem determina manifestul, continuăm fără să blocăm
        manifest_path = None

    repo_dir = os.path.dirname(file_paths[0])
    try:
        g = git.Repo(repo_dir, search_parent_directories=True)
    except Exception as e:
        raise Exception(f"Nu s-a găsit un repository Git valid pentru {repo_dir}: {e}") from e

    # Stage files (relativ la working tree)
    rels = [os.path.relpath(p, g.working_tree_dir) for p in file_paths]
    g.index.add(rels)

    # Commit doar dacă sunt schimbări
    if g.is_dirty(index=True, working_tree=True, untracked_files=True):
        g.index.commit(message)
        # Push
        try:
            remote_name = "origin"
            branch = repo.repo_branch or g.active_branch.name
            remote = g.remote(remote_name)
            # Alegem metoda pe baza tipului de credentiale
            if getattr(repo, "credential_type", False) == "ssh" and getattr(repo, "ssh_key", False):
                _push_with_ssh_key(g, remote, branch, repo.ssh_key)
            elif (
                getattr(repo, "credential_type", False) == "https"
                and getattr(repo, "username", False)
                and getattr(repo, "password", False)
            ):
                _push_with_https(g, remote, branch, repo.username, repo.password)
            else:
                # fără credențiale explicite — încercăm push normal
                remote.push(refspec=f"HEAD:{branch}")
        except Exception:
            # ignorăm eșecurile de push; commit local rămâne
            pass
