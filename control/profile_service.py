import base64, io, requests

from PIL import Image

GRAPH = "https://graph.microsoft.com/v1.0"


def get_profile(access_token: str):
    req = requests.get(f"{GRAPH}/me", headers={"Authorization": f"Bearer {access_token}"}, timeout=5)
    req.raise_for_status()
    return req.json()

def get_photo(access_token: str):
    req = requests.get(f"{GRAPH}/me/photo/$value", headers={"Authorization": f"Bearer {access_token}"}, timeout=5)
    if req.status_code == 200:
        return req.content
    return None
