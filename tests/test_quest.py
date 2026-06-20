from __future__ import annotations

from game.systems.quest import QuestSystem, STARTER_QUEST_FLAGS


def test_starter_quest_starts_tracks_flags_and_completes_once() -> None:
    quest = QuestSystem()

    started = quest.talk_to_starter()

    assert "Cook food" in started.feedback
    assert quest.state.started is True

    for flag in STARTER_QUEST_FLAGS:
        quest.record(flag)

    completed = quest.talk_to_starter()

    assert completed.completed is True
    assert "Quest complete" in completed.feedback

    after = quest.talk_to_starter()

    assert after.completed is False
    assert "safer" in after.feedback


def test_quest_state_round_trip() -> None:
    quest = QuestSystem()
    quest.talk_to_starter()
    quest.record("cooked_food")
    quest.record("used_shop")

    loaded = QuestSystem()
    loaded.load_dict(quest.to_dict())

    assert loaded.state.started is True
    assert loaded.state.flags == {"cooked_food", "used_shop"}


def test_starter_quest_objective_tracks_next_step_and_completion() -> None:
    quest = QuestSystem()

    objective = quest.current_objective()

    assert objective.text == "Talk to the Village Guide."
    assert objective.completed is False

    quest.talk_to_starter()

    assert quest.current_objective().text == "Starter path 0/8: Cook food."

    quest.record("cooked_food")

    assert quest.current_objective().text == "Starter path 1/8: Smelt a bar."

    for flag in STARTER_QUEST_FLAGS:
        quest.record(flag)

    objective = quest.current_objective()

    assert objective.text == "Return to the Village Guide."
    assert objective.completed is False

    quest.talk_to_starter()

    objective = quest.current_objective()

    assert objective.text == "Starter path complete."
    assert objective.completed is True
