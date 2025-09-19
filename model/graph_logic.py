import os, json, msal
from pathlib import Path

TENANT_ID = "99857259-7d6a-47fb-a35b-7f6004c4965d"
CLIENT_ID = "79633382-952d-4e11-bd6d-6f047bf5732b"

SCOPES = ["Mail.ReadWrite", "User.Read"]

CACHE_PATH = Path.home() / ".jobscan_token_cache.json"

def _load_cache():
    cache = msal.SerializableTokenCache()
    if CACHE_PATH.exists():
        cache.deserialize(CACHE_PATH.read_text())
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        CACHE_PATH.write_text(cache.serialize())

def _app(cache):
    return msal.PublicClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        token_cache=cache
    )

def acquire_token_silent():
    cache = _load_cache()
    app = _app(cache)
    accts = app.get_accounts()
    if accts:
        result = app.acquire_token_silent(SCOPES, account=accts[0])
        if result and "access_token" in result:
            _save_cache(cache)
            return result
    return None

def acquire_token_interactive():
    cache = _load_cache()
    app = _app(cache)
    result = app.acquire_token_interactive(scopes=SCOPES)
    _save_cache(cache)
    return result

# Backward-compatible wrapper (if you still call acquire_token())
def acquire_token(silent_only=False):
    if silent_only:
        return acquire_token_silent()
    return acquire_token_silent() or acquire_token_interactive()

def sign_out():
    if CACHE_PATH.exists():
        CACHE_PATH.unlink(missing_ok=True)