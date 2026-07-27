from mycelium_marketing.guardrails import assert_autopilot_allowed, check_content


def test_ok_body():
    text = "I built Mycelium as a local codebase index, not a chat diary."
    assert check_content(text).ok


def test_bans_chat_memory_pitch():
    r = check_content("Our chat memory vault remembers everything")
    assert not r.ok
    # Contrastive positioning is allowed
    r2 = check_content("Mycelium: local index (not a chat memory vault)")
    assert r2.ok


def test_percent_needs_illustrative():
    r = check_content("Save 90% tokens every session")
    assert not r.ok
    r2 = check_content("Illustrative 90% token savings until Impact numbers publish")
    assert r2.ok


def test_reddit_disclosure():
    r = check_content("Cool tool link", require_disclosure=True)
    assert not r.ok
    r2 = check_content("I built this — cool tool", require_disclosure=True)
    assert r2.ok


def test_autopilot_gate():
    assert not assert_autopilot_allowed(i_understand=False, env_flag=None).ok
    assert assert_autopilot_allowed(i_understand=True, env_flag=None).ok
    assert assert_autopilot_allowed(i_understand=False, env_flag="1").ok
