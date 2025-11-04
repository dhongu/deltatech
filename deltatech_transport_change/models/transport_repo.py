import ast
import logging
import os
import shutil
import tempfile
from urllib.parse import quote, urlsplit, urlunsplit

from odoo import fields, models
from odoo.exceptions import UserError

try:
    import git  # GitPython
except Exception:  # pragma: no cover
    git = None

_logger = logging.getLogger(__name__)


class TransportRepo(models.Model):
    _name = "transport.repo"
    _description = "Transport Repository Configuration"

    name = fields.Char(required=True, string="Repository Name")
    module_name = fields.Char(required=True, string="Module Code", help="Folded module name from repository")
    repo_url = fields.Char(required=True, string="Git URL")
    repo_branch = fields.Char(required=True, string="Branch")
    credential_type = fields.Selection([("ssh", "SSH Key"), ("https", "HTTPS")], default="ssh")
    ssh_key = fields.Binary(string="SSH Private Key")
    username = fields.Char(string="Git Username")
    password = fields.Char(string="Git Token / Password")
    repo_local_path = fields.Char(string="Local Path")

    # ========= Repo operations (moved from transport_utils) =========
    def _non_interactive_env(self):
        return {"GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "true"}

    def _credentialized_url(self, base_url: str):
        split = urlsplit(base_url)
        if split.scheme not in ("http", "https"):
            raise UserError("Remote URL must be HTTPS to use token authentication.")
        safe_user = quote((self.username or ""), safe="")
        safe_pass = quote((self.password or ""), safe="")
        netloc = split.hostname or ""
        if split.port:
            netloc = f"{netloc}:{split.port}"
        auth_netloc = f"{safe_user}:{safe_pass}@{netloc}"
        return urlunsplit((split.scheme, auth_netloc, split.path, split.query, split.fragment))

    def clone_to_temp(self):
        self.ensure_one()
        if git is None:
            raise UserError("GitPython (package 'GitPython') is not installed.")
        if self.credential_type != "https" or not self.username or not self.password:
            raise UserError("Repository must be configured for HTTPS with username and token (password).")
        tmp_dir = tempfile.mkdtemp(prefix="odoo_transport_clone_")
        try:
            cred_url = self._credentialized_url(self.repo_url)
            _logger.info("[Transport] Cloning %s branch %s into %s", self.repo_url, self.repo_branch, tmp_dir)
            with git.Git().custom_environment(**self._non_interactive_env()):
                try:
                    repo_obj = git.Repo.clone_from(cred_url, tmp_dir, branch=self.repo_branch, single_branch=True)
                except Exception:
                    repo_obj = git.Repo.clone_from(cred_url, tmp_dir)
            # restore origin url without credentials
            with repo_obj.git.custom_environment(**self._non_interactive_env()):
                origin = repo_obj.remote("origin")
                origin.set_url(self.repo_url)
            # checkout/create branch
            with repo_obj.git.custom_environment(**self._non_interactive_env()):
                if self.repo_branch in [h.name for h in repo_obj.heads]:
                    repo_obj.git.checkout(self.repo_branch)
                else:
                    remote_ref = None
                    try:
                        for r in repo_obj.remotes.origin.refs:
                            if r.name.endswith(f"/{self.repo_branch}"):
                                remote_ref = r
                                break
                    except Exception:
                        remote_ref = None
                    if remote_ref is not None:
                        new_head = repo_obj.create_head(self.repo_branch, remote_ref)
                        new_head.set_tracking_branch(remote_ref)
                        new_head.checkout()
                    else:
                        new_head = repo_obj.create_head(self.repo_branch)
                        new_head.checkout()
            return tmp_dir, repo_obj
        except Exception:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            raise

    def write_csv_and_update_manifest(self, repo_root: str, filename: str, data_content: str):
        """Write CSV under cloned repo and ensure manifest references it. Returns
        (csv_abs_path, manifest_abs_path, manifest_changed: bool, rel_manifest_path)
        """
        sanitized = filename.strip().lstrip("/").replace("\\", "/")
        parts = [p for p in sanitized.split("/") if p not in ("", ".", "..")]
        if not parts:
            raise UserError("Invalid export filename.")
        rel_manifest_path = os.path.join("data", *parts)
        module_root = os.path.join(repo_root, self.module_name)
        os.makedirs(os.path.dirname(os.path.join(module_root, rel_manifest_path)), exist_ok=True)
        csv_abs_path = os.path.join(module_root, rel_manifest_path)
        with open(csv_abs_path, "w", encoding="utf-8", newline="") as f:
            f.write(data_content)
        manifest_abs_path, changed = self._ensure_manifest_has_data_at(module_root, rel_manifest_path)
        return csv_abs_path, manifest_abs_path, changed, rel_manifest_path

    def _ensure_manifest_has_data_at(self, module_root_path: str, rel_manifest_path: str):
        manifest_path = os.path.join(module_root_path, "__manifest__.py")
        if not os.path.exists(manifest_path):
            raise UserError(f"__manifest__.py was not found in {module_root_path}.")
        with open(manifest_path, encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content)
        dict_node = None
        if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Dict):
            dict_node = tree.body[0].value
        elif tree.body and isinstance(tree.body[0], ast.Assign) and isinstance(tree.body[0].value, ast.Dict):
            dict_node = tree.body[0].value
        if dict_node is None:
            raise UserError("The structure of __manifest__.py could not be parsed as a dict.")
        manifest_dict = ast.literal_eval(dict_node)
        data_list = manifest_dict.get("data") or []
        if rel_manifest_path not in data_list:
            data_list.append(rel_manifest_path)
            manifest_dict["data"] = data_list
            import pprint

            rendered = pprint.pformat(manifest_dict, width=120, sort_dicts=False) + "\n"
            with open(manifest_path, "w", encoding="utf-8") as f:
                f.write(rendered)
            return manifest_path, True
        return manifest_path, False

    def commit_and_push(self, repo_obj, commit_message: str):
        self.ensure_one()
        with repo_obj.git.custom_environment(**self._non_interactive_env()):
            repo_obj.git.add(A=True)
            if repo_obj.is_dirty(index=True, working_tree=True, untracked_files=True):
                repo_obj.index.commit(commit_message)
                try:
                    origin = repo_obj.remote("origin")
                except Exception as e:
                    raise UserError("No 'origin' remote configured in cloned repo.") from e
                # determine if tracking exists
                try:
                    tracking = repo_obj.head.reference.tracking_branch()
                except Exception:
                    tracking = None
                # temporarily set credentialized url and push
                cred_url = self._credentialized_url(list(origin.urls)[0])
                try:
                    origin.set_url(cred_url)
                    if tracking is None:
                        repo_obj.git.push("--set-upstream", "origin", self.repo_branch)
                    else:
                        origin.push(refspec=f"HEAD:{self.repo_branch}")
                finally:
                    origin.set_url(self.repo_url)
            else:
                _logger.info("[Transport] No changes to commit in temp repo %s", repo_obj.working_tree_dir)
