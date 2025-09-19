import base64
import json

from PyQt6.QtCore import QSettings

SETTINGS = QSettings("Tyler Builds", "JobScan")


def save_user_profile(display_name: str, email: str, photo_bytes: bytes|None):
    data = {
        "signedIn": True,
        "displayName": display_name,
        "email": email,
        "hasPhoto": bool(photo_bytes),
        "photoBytes": base64.b64encode(photo_bytes).decode("ascii") if photo_bytes else "",
    }
    SETTINGS.setValue("user/profile", json.dumps(data))


def load_user_profile() -> dict|None:
    raw = SETTINGS.value("user/profile", "")
    if not raw:
        return None
    try:
        data = json.loads(raw)
        data.setdefault("signedIn", False)
        data.setdefault("hasPhoto", False)
        data.setdefault("photoBytes", '')
        return data
    except Exception:
        return None

def clear_user_profile():
    SETTINGS.remove("user/profile")