from __future__ import annotations

from collections.abc import Callable
import logging
from typing import Any

from direct.gui.DirectGui import DirectButton, DirectEntry, DirectFrame, DirectLabel
from direct.showbase.DirectObject import DirectObject

from game import settings
from game.engine import auth, save
from game.style import UiPalette as UI


LOGGER = logging.getLogger(__name__)

PANEL = UI.PANEL
PANEL_DARK = UI.PANEL_DARK
BUTTON = UI.BUTTON
BUTTON_HOVER = UI.BUTTON_HOVER
TEXT = UI.TEXT
GOLD = UI.GOLD

DEFAULT_LOGIN_USERNAME = "donny101"
DEFAULT_LOGIN_PASSWORD = "donny101"


class LoginScreen(DirectObject):
    def __init__(
        self,
        app: Any,
        on_success: Callable[[str, dict[str, Any], str], None],
    ) -> None:
        DirectObject.__init__(self)
        self.app = app
        self.on_success = on_success
        self.widgets: list[Any] = []
        self._build()

    def set_status(self, message: str) -> None:
        self.status["text"] = message

    def destroy(self) -> None:
        self.ignoreAll()
        for widget in self.widgets:
            widget.destroy()
        self.widgets.clear()

    def _build(self) -> None:
        backdrop = DirectFrame(
            frameColor=(0.04, 0.05, 0.07, 0.84),
            frameSize=(-2.0, 2.0, -1.25, 1.25),
        )
        shadow = DirectFrame(
            parent=backdrop,
            frameColor=(0.0, 0.0, 0.0, 0.32),
            frameSize=(-0.71, 0.71, -0.46, 0.46),
            pos=(0.03, 0, -0.03),
        )
        frame = DirectFrame(
            parent=backdrop,
            frameColor=UI.STONE,
            frameSize=(-0.68, 0.68, -0.43, 0.43),
        )
        inset = DirectFrame(
            parent=frame,
            frameColor=PANEL,
            frameSize=(-0.64, 0.64, -0.39, 0.39),
        )
        title_shadow = DirectFrame(
            parent=frame,
            frameColor=(0.0, 0.0, 0.0, 0.20),
            frameSize=(-0.44, 0.44, 0.20, 0.31),
            pos=(0.01, 0, -0.01),
        )
        title_strip = DirectFrame(
            parent=frame,
            frameColor=UI.PARCHMENT,
            frameSize=(-0.44, 0.44, 0.21, 0.32),
        )
        title_accent = DirectFrame(
            parent=frame,
            frameColor=UI.GOLD,
            frameSize=(-0.22, 0.22, -0.01, 0.01),
            pos=(0, 0, 0.225),
        )
        title = DirectLabel(
            parent=frame,
            text="Hearthvale",
            scale=0.082,
            pos=(0, 0, 0.27),
            frameColor=(0, 0, 0, 0),
            text_fg=GOLD,
        )
        subtitle = DirectLabel(
            parent=frame,
            text="Local saves only",
            scale=0.031,
            pos=(0, 0, 0.205),
            frameColor=(0, 0, 0, 0),
            text_fg=UI.MUTED_TEXT,
        )
        username_label = DirectLabel(
            parent=frame,
            text="Username",
            scale=0.036,
            pos=(-0.34, 0, 0.18),
            frameColor=(0, 0, 0, 0),
            text_fg=TEXT,
        )
        self.username = DirectEntry(
            parent=frame,
            initialText=DEFAULT_LOGIN_USERNAME,
            width=18,
            scale=0.051,
            pos=(-0.46, 0, 0.11),
            frameColor=PANEL_DARK,
            text_fg=TEXT,
            focus=1,
            command=self._login,
        )
        password_label = DirectLabel(
            parent=frame,
            text="Password",
            scale=0.036,
            pos=(-0.34, 0, 0.04),
            frameColor=(0, 0, 0, 0),
            text_fg=TEXT,
        )
        self.password = DirectEntry(
            parent=frame,
            initialText=DEFAULT_LOGIN_PASSWORD,
            width=18,
            scale=0.051,
            pos=(-0.46, 0, -0.03),
            frameColor=PANEL_DARK,
            text_fg=TEXT,
            obscured=1,
            focus=0,
            command=self._login,
        )
        login_button = DirectButton(
            parent=frame,
            text="Login",
            scale=0.058,
            pos=(-0.18, 0, -0.18),
            frameColor=(BUTTON, BUTTON_HOVER, BUTTON_HOVER, BUTTON),
            text_fg=TEXT,
            command=self._login,
        )
        register_button = DirectButton(
            parent=frame,
            text="Register",
            scale=0.048,
            pos=(0.20, 0, -0.18),
            frameColor=(BUTTON, BUTTON_HOVER, BUTTON_HOVER, BUTTON),
            text_fg=TEXT,
            command=self._register,
        )
        quit_button = DirectButton(
            parent=frame,
            text="Quit",
            scale=0.042,
            pos=(0, 0, -0.28),
            frameColor=(PANEL_DARK, BUTTON, BUTTON_HOVER, PANEL_DARK),
            text_fg=TEXT,
            command=self.app.userExit,
        )
        self.status = DirectLabel(
            parent=frame,
            text="Prefilled local test account",
            scale=0.034,
            pos=(0, 0, -0.37),
            frameColor=(0, 0, 0, 0),
            text_fg=GOLD,
        )
        self.widgets.extend([
            backdrop,
            shadow,
            frame,
            inset,
            title_shadow,
            title_strip,
            title_accent,
            title,
            subtitle,
            username_label,
            self.username,
            password_label,
            self.password,
            login_button,
            register_button,
            quit_button,
            self.status,
        ])
        self._bind_tab_navigation()

    def _bind_tab_navigation(self) -> None:
        self.accept("tab", self._focus_password)
        self.accept("shift-tab", self._focus_username)

    def _focus_username(self) -> None:
        self._focus_entry(self.username, self.password)

    def _focus_password(self) -> None:
        self._focus_entry(self.password, self.username)

    @staticmethod
    def _focus_entry(focused: Any, blurred: Any) -> None:
        blurred["focus"] = 0
        focused["focus"] = 1

    def _credentials(self) -> tuple[str, str] | None:
        username = self.username.get().strip()
        password = self.password.get()
        if not username or not password:
            self.set_status("Enter a username and password")
            return None
        return username, password

    def _login(self, *_args: object) -> None:
        credentials = self._credentials()
        if credentials is None:
            return
        username, password = credentials
        try:
            account = auth.login_user(username, password, settings.USERS_DB_PATH)
        except ValueError as exc:
            self.set_status(str(exc))
            return
        except OSError:
            LOGGER.exception("Login failed")
            self.set_status("Login failed")
            return

        if account is None:
            self.set_status("Invalid username or password")
            return
        self._enter(account.username, "Logged in")

    def _register(self) -> None:
        credentials = self._credentials()
        if credentials is None:
            return
        username, password = credentials
        try:
            account = auth.register_user(username, password, settings.USERS_DB_PATH)
        except auth.UsernameAlreadyExists:
            self.set_status("Username already exists")
            return
        except ValueError as exc:
            self.set_status(str(exc))
            return
        except OSError:
            LOGGER.exception("Registration failed")
            self.set_status("Registration failed")
            return
        self._enter(account.username, "Registered new account")

    def _enter(self, username: str, message: str) -> None:
        try:
            state, created = save.load_or_create_save(username, settings.SAVES_DIR)
        except OSError:
            LOGGER.exception("Save load failed for %s", username)
            self.set_status("Could not load save")
            return

        self.destroy()
        detail = "New character created" if created else message
        self.on_success(username, state, detail)
