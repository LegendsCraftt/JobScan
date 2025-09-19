import os, json, base64, webbrowser, time
import msal, requests
from urllib.parse import quote
import multiprocessing as mp
import winreg

from PyQt6.QtWidgets import QMessageBox

TENANT_ID = "99857259-7d6a-47fb-a35b-7f6004c4965d"
CLIENT_ID = "79633382-952d-4e11-bd6d-6f047bf5732b"
SCOPES    = ["Mail.ReadWrite"]


def has_classic_outlook() -> bool:
    """Return True if classic Outlook's OUTLOOK.EXE is installed."""
    candidates = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\OUTLOOK.EXE"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\OUTLOOK.EXE"),
        (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\OUTLOOK.EXE"),
    ]
    for hive, key_path in candidates:
        try:
            with winreg.OpenKey(hive, key_path) as k:
                path, _ = winreg.QueryValueEx(k, None)
                if path and os.path.exists(path):
                    return True
        except OSError:
            continue
    return False

def _try_graph(to, subject, body, attachment_path, access_token: str|None) -> bool:
    try:
        if access_token:
            link = _graph_create_draft_link_with_token(
                access_token, to, subject, body, attachment_path
            )
        else:
            link = _graph_create_draft_link(to, subject, body, attachment_path)

        if link:
            print("[compose] Graph webLink:", link)
            webbrowser.open(link)
            return True

    except Exception as e:
        print("[compose] Graph error:", repr(e))
    return False

def _graph_create_draft_link_with_token(access_token, to, subject, body, attachment_path):
    msg = {
        "subject": subject or "",
        "body": {"contentType": "Text", "content": body or ""},
        "toRecipients": [{"emailAddress": {"address": a}} for a in (to or [])],
        "attachments": []
    }
    if attachment_path and os.path.isfile(attachment_path):
        with open(attachment_path, "rb") as f:
            msg["attachments"].append({
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": os.path.basename(attachment_path),
                "contentBytes": base64.b64encode(f.read()).decode("ascii")
            })

    r = requests.post(
        "https://graph.microsoft.com/v1.0/me/messages",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        data=json.dumps(msg),
        timeout=30
    )
    r.raise_for_status()
    draft = r.json()
    link = draft.get("webLink")
    if not link:
        raise RuntimeError("Draft created but no webLink returned")
    return f"{link}{'&' if '?' in link else '?'}ispopout=1"

def _graph_create_draft_link(to, subject, body, attachment_path):

    # --- simple persistent token cache so users don’t re-auth every time ---
    cache_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.getcwd()), "MFC-ComposeHelper")
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, "msal_cache.bin")

    token_cache = msal.SerializableTokenCache()
    if os.path.exists(cache_path):
        try:
            token_cache.deserialize(open(cache_path, "r", encoding="utf-8").read())
        except Exception:
            pass

    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        token_cache=token_cache
    )

    # Try silent first
    accounts = app.get_accounts()
    result = app.acquire_token_silent(SCOPES, account=accounts[0] if accounts else None)

    # Interactive fallback; then device-code fallback
    if not result or "access_token" not in result:
        result = app.acquire_token_interactive(SCOPES)
        if not result or "access_token" not in result:
            flow = app.initiate_device_flow(scopes=SCOPES)
            if "user_code" not in flow:
                raise RuntimeError("Device flow start failed")
            print(f"[compose] To sign in, visit {flow['verification_uri']} and enter code: {flow['user_code']}")
            result = app.acquire_token_by_device_flow(flow)

    # Persist cache if changed
    if token_cache.has_state_changed:
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(token_cache.serialize())

    access = result["access_token"]

    msg = {
        "subject": subject or "",
        "body": {"contentType": "Text", "content": body or ""},
        "toRecipients": [{"emailAddress": {"address": a}} for a in (to or [])],
        "attachments": []
    }

    if attachment_path and os.path.isfile(attachment_path):
        with open(attachment_path, "rb") as f:
            msg["attachments"].append({
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": os.path.basename(attachment_path),
                "contentBytes": base64.b64encode(f.read()).decode("ascii")
            })

    r = requests.post(
        "https://graph.microsoft.com/v1.0/me/messages",
        headers={"Authorization": f"Bearer {access}", "Content-Type": "application/json"},
        data=json.dumps(msg),
        timeout=30
    )
    r.raise_for_status()
    draft = r.json()
    link = draft.get("webLink")
    if not link:
        raise RuntimeError("Draft created but no webLink returned")
    sep = "&" if "?" in link else "?"
    link = f"{link}{sep}ispopout=1"
    return link

# ---------- Classic Outlook (COM) with timeout ----------
def _com_worker(to, subject, body, attachment_path, q):
    try:
        import win32com.client as win32, os
        ol = win32.Dispatch("Outlook.Application")
        mail = ol.CreateItem(0)  # olMailItem
        if to:      mail.To = ";".join(to)
        if subject: mail.Subject = subject
        if body:    mail.Body = body
        if attachment_path and os.path.isfile(attachment_path):
            mail.Attachments.Add(Source=os.path.abspath(attachment_path))
        mail.Display(False)
        q.put(True)
    except Exception as e:
        q.put(("[COM] " + repr(e)))

def _try_com_with_timeout(to, subject, body, attachment_path, timeout: float) -> bool:
    q = mp.Queue()
    p = mp.Process(target=_com_worker, args=(to, subject, body, attachment_path, q))
    p.start()
    p.join(timeout)
    if p.is_alive():
        p.terminate(); p.join(0.5)
        print("[compose] COM startup timed out (likely new Outlook or a modal first-run dialog).")
        return False
    if not q.empty():
        res = q.get()
        if res is True:
            return True
        else:
            print("[compose]", res)
    return False

# ---------- mailto: fallback (no attachments) ----------
def _mailto_open(to, subject, body):
    addr = ",".join(to or [])
    qs = []
    if subject: qs.append("subject=" + quote(subject))
    if body:    qs.append("body=" + quote(body))
    url = "mailto:" + addr + ("?" + "&".join(qs) if qs else "")
    webbrowser.open(url)


def compose(
        version='new',
        to=None,
        subject="",
        body="",
        attachment_path=None,
        access_token: str|None =None,
):
    try:
        if version == 'new':

            _try_graph(to, subject, body, attachment_path, access_token=access_token)
            print("[compose] Used Graph (new Outlook path).")
            return True

        elif version == 'old':

            if not has_classic_outlook():
                _mailto_open(to, subject, body)
                print("[compose] Used mailto: fallback (no attachment) (doesn't have outlook installed).")
                return True

            _try_com_with_timeout(to, subject, body, attachment_path, timeout=20.0)
            print("[compose] Used classic Outlook (COM).")
            return True

        else:
            raise ValueError(f"Invalid version: {version}")

    except Exception as e:
        print("[compose] Error:", repr(e))
        return False



