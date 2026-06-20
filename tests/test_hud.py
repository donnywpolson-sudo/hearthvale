from __future__ import annotations

from game.ui import hud


class FakeWidget:
    def __init__(self, *args, **kwargs) -> None:
        self.options = dict(kwargs)
        self.destroyed = False
        self.hidden = False
        self.text = self.options.get("text", "")
        self.pos = self.options.get("pos")

    def setText(self, text: str) -> None:
        self.text = text

    def setPos(self, *pos) -> None:
        self.pos = pos
        self.options["pos"] = pos

    def hide(self) -> None:
        self.hidden = True

    def show(self) -> None:
        self.hidden = False

    def destroy(self) -> None:
        self.destroyed = True

    def __getitem__(self, key: str):
        return self.options[key]

    def __setitem__(self, key: str, value) -> None:
        self.options[key] = value
        if key == "text":
            self.text = value
        elif key == "pos":
            self.pos = value

    def click(self) -> None:
        command = self.options.get("command")
        if command is not None:
            command()


class FakeOnscreenText(FakeWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.may_change = bool(self.options.get("mayChange")) or not self.text

    def setPos(self, *pos) -> None:
        if not self.may_change:
            raise AssertionError("static OnscreenText cannot be repositioned")
        super().setPos(*pos)


def test_inventory_grid_has_fixed_slots_and_populates_in_category_order(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(_items())

    assert len(ui.inventory_slots) == hud.INVENTORY_SLOT_COUNT
    assert all(not slot.button.hidden for slot in ui.inventory_slots)

    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={
            "mystery_item": 1,
            "raw_shrimp": 4,
            "copper_ore": 6,
            "logs": 3,
            "coins": 12,
        },
        bank={},
        skills=FakeSkills(),
    )

    assert [slot.item_id for slot in ui.inventory_slots[:5]] == [
        "coins",
        "logs",
        "copper_ore",
        "raw_shrimp",
        "mystery_item",
    ]
    assert ui.inventory_slots[0].button.text == "12"
    assert ui.inventory_slots[1].button.text == "3"
    assert ui.inventory_slots[0].button.options["text_scale"] == hud.INVENTORY_QUANTITY_TEXT_SCALE
    assert any(not part.hidden for part in ui.inventory_slots[0].icon.parts)
    assert ui.inventory_slots[5].item_id is None
    assert ui.inventory_slots[5].button.text == ""
    assert all(part.hidden for part in ui.inventory_slots[5].icon.parts)


def test_inventory_slots_use_select_item_callback(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    selected: list[str] = []
    ui = hud.Hud(_items(), on_select_item=selected.append)
    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={"raw_shrimp": 4},
        bank={},
        skills=FakeSkills(),
    )

    ui.inventory_slots[0].button.click()
    ui.inventory_slots[1].button.click()

    assert selected == ["raw_shrimp"]


def test_side_tabs_switch_visible_content(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(_items())

    assert ui.active_tab == hud.INVENTORY_TAB
    assert ui.tab_frames[hud.INVENTORY_TAB].hidden is False
    assert ui.tab_frames[hud.CLOTHES_TAB].hidden is True
    assert ui.tab_frames[hud.SKILLS_TAB].hidden is True

    ui.tab_buttons[hud.SKILLS_TAB].click()

    assert ui.active_tab == hud.SKILLS_TAB
    assert ui.tab_frames[hud.INVENTORY_TAB].hidden is True
    assert ui.tab_frames[hud.CLOTHES_TAB].hidden is True
    assert ui.tab_frames[hud.SKILLS_TAB].hidden is False
    assert ui.tab_buttons[hud.SKILLS_TAB].options["frameColor"][0] == hud.SLOT_HILITE


def test_selected_inventory_slot_is_highlighted(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    ui = hud.Hud(_items())

    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={"raw_shrimp": 4, "logs": 3},
        bank={},
        selected_item_id="raw_shrimp",
        skills=FakeSkills(),
    )

    assert ui.inventory_slots[0].item_id == "logs"
    assert ui.inventory_slots[0].button.options["frameColor"][0] == hud.SLOT
    assert ui.inventory_slots[1].item_id == "raw_shrimp"
    assert ui.inventory_slots[1].button.options["frameColor"][0] == hud.SLOT_HILITE


def test_bank_rows_show_positive_inventory_or_bank_stacks(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)

    ui = hud.Hud(
        {
            "logs": {"name": "Logs", "category": "wood"},
            "copper_ore": {"name": "Copper ore", "category": "ore"},
        }
    )

    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={"logs": 3, "copper_ore": 6},
        bank={"logs": 0},
        skills=FakeSkills(),
    )

    assert list(ui.bank_rows) == ["logs", "copper_ore"]
    assert ui.bank_rows["logs"].bank_label.text == "3/0"
    assert ui.bank_rows["copper_ore"].bank_label.text == "6/0"
    assert ui.empty_bank_label.hidden is True

    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={"logs": 3, "copper_ore": 6},
        bank={"logs": 2},
        skills=FakeSkills(),
    )

    assert list(ui.bank_rows) == ["logs", "copper_ore"]
    assert ui.bank_rows["logs"].bank_label.text == "3/2"
    assert ui.empty_bank_label.hidden is True

    row = ui.bank_rows["logs"]
    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={"copper_ore": 6},
        bank={"logs": 0},
        skills=FakeSkills(),
    )

    assert list(ui.bank_rows) == ["copper_ore"]
    assert row.bank_label.destroyed is True
    assert ui.empty_bank_label.hidden is True


def test_shop_rows_show_stock_and_buy_callback(monkeypatch) -> None:
    _install_hud_fakes(monkeypatch)
    bought: list[str] = []
    items = {
        **_items(),
        "bronze_axe": {"name": "Bronze axe", "category": "tool", "sell_price": 8},
    }
    ui = hud.Hud(items, on_buy_item=bought.append)

    ui.update(
        account="test",
        time_text="Day 1 08:00",
        selected_text="Selected: none",
        inventory={"coins": 30},
        bank={},
        skills=FakeSkills(),
        shop_stock=[{"item_id": "bronze_axe", "price": 25}],
    )

    assert list(ui.shop_rows) == ["bronze_axe"]
    assert ui.shop_rows["bronze_axe"].quantity_label.text == "0"
    assert ui.shop_rows["bronze_axe"].price_label.text == "25"
    assert ui.shop_coin_label.text == "Coins: 30"

    ui.shop_rows["bronze_axe"].action_button.click()

    assert bought == ["bronze_axe"]


class FakeSkills:
    def get(self, _skill_name: str) -> FakeSkill:
        return FakeSkill()


class FakeSkill:
    level = 1
    xp = 0


def _install_hud_fakes(monkeypatch) -> None:
    monkeypatch.setattr(hud, "DirectFrame", FakeWidget)
    monkeypatch.setattr(hud, "DirectButton", FakeWidget)
    monkeypatch.setattr(hud, "OnscreenText", FakeOnscreenText)


def _items() -> dict[str, dict[str, object]]:
    return {
        "coins": {"name": "Coins", "category": "currency"},
        "logs": {"name": "Logs", "category": "wood"},
        "copper_ore": {"name": "Copper ore", "category": "ore"},
        "raw_shrimp": {
            "name": "Raw shrimp",
            "category": "fish",
            "cook_result": "cooked_shrimp",
        },
        "mystery_item": {"name": "Mystery item"},
    }
