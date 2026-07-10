from app.plans import POCKET_TIERS, VIP_PLANS, resolve_plan, resolve_stars


def test_resolve_vip():
    assert resolve_plan("vip", "1month") == ("VIP 1 Месяц", 45.0)
    assert resolve_plan("vip", "lifetime") == ("VIP Навсегда", 199.0)
    assert resolve_plan("vip", "nope") is None


def test_resolve_pocket():
    assert resolve_plan("pocket", "0") == ("PocketOption 65$→87$", 65.0)
    assert resolve_plan("pocket", "2")[1] == 230.0
    assert resolve_plan("pocket", "99") is None
    assert resolve_plan("pocket", "abc") is None


def test_resolve_stars_payloads():
    name, stars, payload = resolve_stars("vip", "3months")
    assert stars == VIP_PLANS["3months"].stars and payload == "vip_3months"
    name, stars, payload = resolve_stars("pocket", "1")
    assert stars == POCKET_TIERS[1].stars and payload == "pocket_1"
    assert resolve_stars("vip", "bad") is None
