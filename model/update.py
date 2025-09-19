# --- update.py (add/replace) ---
import os, json, contextlib
import pathlib, tempfile, subprocess, requests
from packaging.version import Version
from version import __version__ as CURRENT

OWNER, REPO = "LegendsCraftt", "JobScan"

APP_ID = "JobScan"
APPDATA = pathlib.Path(os.getenv("LOCALAPPDATA", tempfile.gettempdir())) / APP_ID
APPDATA.mkdir(parents=True, exist_ok=True)
MARKER = APPDATA / "pending_update.json"

def _headers(api=False, bin=False):
    h = {"User-Agent": "JobScan-Updater"}
    if api: h["Accept"] = "application/vnd.github+json"
    if bin: h["Accept"] = "application/octet-stream"
    return h

def get_latest_release():
    r = requests.get(
        f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest",
        headers=_headers(api=True), timeout=10
    )
    r.raise_for_status()
    return r.json()

def pick_installer(rel_json):
    for a in rel_json.get("assets", []):
        if a["name"].lower().endswith((".exe", ".msi")):
            return a["name"], a["browser_download_url"]
    return None, None

def download_installer_with_progress(url: str, dest_path: str, progress_cb=None):
    with requests.get(url, headers=_headers(bin=True), stream=True, timeout=30) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", "0") or 0)
        done = 0
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(65536):
                if not chunk:
                    continue
                f.write(chunk)
                done += len(chunk)
                if progress_cb and total:
                    progress_cb(int(done * 100 / total))

def check_latest_against_current():
    """Return {'name','url','version'} if an update exists, else None."""
    rel = get_latest_release()
    remote = rel["tag_name"].lstrip("vV")
    if Version(remote) <= Version(CURRENT):
        print(f"[update] Current version {CURRENT} is up-to-date.")
        return None
    name, url = pick_installer(rel)
    if not url:
        return None
    return {"name": name, "url": url, "version": remote}

def run_installer_silent(installer_path: str):
    if installer_path.lower().endswith(".msi"):
        cmd = ["msiexec", "/i", installer_path, "/qn", "/norestart"]
    else:
        cmd = [installer_path, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-"]
    subprocess.Popen(cmd, close_fds=True)

def apply_pending_update_if_any():
    """If user chose 'Later' last run, apply before UI starts."""
    if not MARKER.exists():
        return
    try:
        data = json.loads(MARKER.read_text(encoding="utf-8"))
        installer = data.get("installer_path")
        if installer and pathlib.Path(installer).exists():
            run_installer_silent(installer)
            raise SystemExit(0)
    except Exception:
        pass
    finally:
        with contextlib.suppress(Exception):
            MARKER.unlink()
