import base64

from PyQt6.QtGui import QPixmap
from io import BytesIO
from PIL import Image
from model.graph_logic import acquire_token, acquire_token_silent, acquire_token_interactive
from control.profile_service import get_profile, get_photo
from model.settings import SETTINGS, load_user_profile, save_user_profile, clear_user_profile


class AuthState:
    def __init__(self):
        self.signed_in = False
        self.photo_pixmap = None
        self.display_name = ''
        self.email = ''

    @staticmethod
    def from_cache(cache: dict):
        state = AuthState()
        if not cache or not cache.get('signedIn'):
            return state

        state.signed_in = True
        state.display_name = cache.get('displayName', '')
        state.email = cache.get('email', '')
        b64 = cache.get('photoBytes', '')
        if b64:
            try:
                raw = base64.b64decode(b64)
                image = Image.open(BytesIO(raw))
                buffer = BytesIO()
                image.save(buffer, format='PNG')
                px = QPixmap()
                px.loadFromData(buffer.getvalue())
                state.photo_pixmap = px
            except Exception:
                state.photo_pixmap = None

        return state

class AuthController:
    def __init__(self, view):
        self.view = view
        self.state = AuthState()

    def bootstrap(self):
        cached = load_user_profile()
        self.state = AuthState.from_cache(cached)
        self.view.controller.render_auth(self.state)

        try:
            token = acquire_token(silent_only=True)
            if token:
                token = token['access_token']
                self.refresh_profile(token, repaint=True)
        except Exception as e:
            pass

    def sign_in_clicked(self):

        try:
            token = acquire_token()
            token = token['access_token']
            if not token:
                raise RuntimeError("No token acquired")
            self.refresh_profile(token, repaint=True)
        except Exception as e:
            self.view.controller._show_popout('Sign in error', str(e), 'warning')


    def refresh_profile(self, access_token: str, repaint: bool):
        prof = get_profile(access_token)
        photo_bytes = get_photo(access_token)

        name = prof.get('displayName', '')
        email = prof.get('mail') or prof.get('userPrincipalName') or ''

        pixmap = None
        if photo_bytes:
            try:
                image = Image.open(BytesIO(photo_bytes))
                buffer = BytesIO()
                image.save(buffer, format='PNG')
                px = QPixmap()
                px.loadFromData(buffer.getvalue())
                pixmap = px
            except Exception:
                pixmap = None

        self.state.signed_in = True
        self.state.display_name = name
        self.state.email = email
        self.state.photo_pixmap = pixmap

        save_user_profile(name, email, photo_bytes)

        if repaint:
            self.view.controller.render_auth(self.state)

    def get_access_token(self, interactive: bool = False):
        token = acquire_token_silent()
        if not token and interactive:
            token = acquire_token_interactive()

        if token and 'access_token' in token:
            return token['access_token']
        return None


    def sign_out_clicked(self):
        from model.graph_logic import sign_out as msal_sign_out
        msal_sign_out()
        clear_user_profile()
        self.state = AuthState()
        print(f'[AuthController] Sign out clicked. User profile cleared. Authstate: {self.state.signed_in}')
        self.view.controller.render_auth(self.state)
        print('[AuthController] Sign out complete. User profile cleared.')