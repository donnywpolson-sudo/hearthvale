from __future__ import annotations

from game.ui import login


class FakeApp:
    def userExit(self) -> None:
        pass


class FakeWidget:
    def __init__(self, *args, **kwargs) -> None:
        self.options = dict(kwargs)
        self.destroyed = False
        self.text = self.options.get("initialText", "")

    def __getitem__(self, key: str):
        return self.options[key]

    def __setitem__(self, key: str, value) -> None:
        self.options[key] = value

    def destroy(self) -> None:
        self.destroyed = True

    def get(self) -> str:
        return self.text


def test_tab_navigation_switches_between_login_entries(monkeypatch) -> None:
    accepted = {}
    ignored = []

    monkeypatch.setattr(login, "DirectFrame", FakeWidget)
    monkeypatch.setattr(login, "DirectLabel", FakeWidget)
    monkeypatch.setattr(login, "DirectEntry", FakeWidget)
    monkeypatch.setattr(login, "DirectButton", FakeWidget)

    def fake_accept(self, event: str, command, *args, **kwargs) -> None:
        accepted[event] = command

    def fake_ignore_all(self) -> None:
        ignored.append(self)

    monkeypatch.setattr(login.LoginScreen, "accept", fake_accept)
    monkeypatch.setattr(login.LoginScreen, "ignoreAll", fake_ignore_all)

    screen = login.LoginScreen(FakeApp(), lambda *_args: None)

    assert screen.username["focus"] == 1
    assert screen.password.options.get("focus", 0) == 0

    accepted["tab"]()

    assert screen.username["focus"] == 0
    assert screen.password["focus"] == 1

    accepted["shift-tab"]()

    assert screen.username["focus"] == 1
    assert screen.password["focus"] == 0

    screen.destroy()

    assert ignored == [screen]
