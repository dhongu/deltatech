"""Update broker for the Terrabit Connect agent.

The agent's repository is private and the agent must NOT hold a GitHub token.
Odoo keeps the token (in ``ir.config_parameter``, server-side) and proxies to the
agent: the agent asks for the version/download with its station key, Odoo calls
GitHub with the token. Generic (suite-neutral) — lives in the TC base module.
"""

import logging

import requests

_logger = logging.getLogger(__name__)

PARAM_REPO = "deltatech_tc.update_repo"
PARAM_TOKEN = "deltatech_tc.update_token"
PARAM_ASSET = "deltatech_tc.update_asset"
DEFAULT_ASSET = "terrabit-connect.jar"

_API = "https://api.github.com"


def _cfg(env, key, default=""):
    return env["ir.config_parameter"].sudo().get_param(key, default)


def _headers(token, accept):
    return {"Authorization": f"Bearer {token}", "Accept": accept, "X-GitHub-Api-Version": "2022-11-28"}


def latest_release(env):
    """Return dict with ``tag``/``version``/``notes``/``assets`` or ``{"error": ...}``."""
    repo = _cfg(env, PARAM_REPO)
    token = _cfg(env, PARAM_TOKEN)
    if not repo or not token:
        return {"error": "Update repository/token not configured in Settings."}
    try:
        resp = requests.get(
            f"{_API}/repos/{repo}/releases/latest",
            headers=_headers(token, "application/vnd.github+json"),
            timeout=30,
        )
    except requests.RequestException as exc:
        return {"error": f"Cannot reach GitHub: {exc}"}
    if resp.status_code != 200:
        return {"error": f"GitHub returned {resp.status_code}."}
    data = resp.json()
    tag = data.get("tag_name") or ""
    return {
        "tag": tag,
        "version": tag.lstrip("v"),
        "notes": data.get("body") or "",
        "assets": data.get("assets") or [],
    }


def download_asset(env, asset_name=None):
    """Download a release asset's bytes. Returns ``(bytes, None)`` or ``(None, err)``."""
    asset_name = asset_name or _cfg(env, PARAM_ASSET, DEFAULT_ASSET)
    info = latest_release(env)
    if info.get("error"):
        return None, info["error"]
    asset = next((a for a in info["assets"] if a.get("name") == asset_name), None)
    if not asset:
        return None, f"Asset {asset_name!r} not found in release {info['tag']}."
    token = _cfg(env, PARAM_TOKEN)
    try:
        resp = requests.get(
            asset["url"],
            headers=_headers(token, "application/octet-stream"),
            timeout=300,
        )
    except requests.RequestException as exc:
        return None, f"Cannot download asset: {exc}"
    if resp.status_code != 200:
        return None, f"GitHub asset download returned {resp.status_code}."
    return resp.content, None
