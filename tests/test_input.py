from __future__ import annotations

from game.engine.input import InputManager


def test_escape_does_not_quit_game() -> None:
    app = _FakeApp()
    input_manager = InputManager(app)

    input_manager.bind()

    assert "escape" in app.accepted
    assert app.accepted["escape"][0] is not app.userExit

    app.accepted["escape"][0]()

    assert app.exit_calls == 0


def test_tab_hotkeys_bind_to_hud_toggles() -> None:
    app = _FakeApp()
    input_manager = InputManager(app)

    input_manager.bind()

    app.accepted["i"][0]()
    app.accepted["c"][0]()
    app.accepted["k"][0]()

    assert app.tab_calls == ["inventory", "clothes", "skills"]


class _FakeApp:
    def __init__(self) -> None:
        self.accepted: dict[str, tuple[object, list[object] | None]] = {}
        self.exit_calls = 0
        self.tab_calls: list[str] = []

    def accept(self, event: str, command, args: list[object] | None = None) -> None:
        self.accepted[event] = (command, args)

    def on_mouse_wheel(self, amount: int) -> None:
        pass

    def on_left_click(self) -> None:
        pass

    def on_right_click(self) -> None:
        pass

    def save_game(self) -> None:
        pass

    def load_game(self) -> None:
        pass

    def toggle_inventory_tab(self) -> None:
        self.tab_calls.append("inventory")

    def toggle_clothes_tab(self) -> None:
        self.tab_calls.append("clothes")

    def toggle_skills_tab(self) -> None:
        self.tab_calls.append("skills")

    def userExit(self) -> None:
        self.exit_calls += 1
