def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_energy_and_devices_api(client):
    today = client.get("/api/energy/today")
    summary = client.get("/api/energy/summary")
    devices = client.get("/api/devices")
    assert today.status_code == 200
    assert summary.status_code == 200
    assert devices.status_code == 200
    today_json = today.json()
    if today_json["series"]:
        assert today_json["total_energy"] > 0
        assert len(devices.json()) >= 1


def test_prediction_anomaly_strategy_profile(client):
    pred = client.get("/api/prediction/hour")
    day = client.get("/api/prediction/day")
    anomalies = client.get("/api/anomalies")
    latest = client.get("/api/anomalies/latest")
    strategies = client.get("/api/strategies")
    top = client.get("/api/strategies/top")
    profile = client.get("/api/profile")
    score = client.get("/api/profile/energy-score")
    potential = client.get("/api/profile/saving-potential")
    for res in (pred, day, anomalies, latest, strategies, top, profile, score, potential):
        assert res.status_code == 200


def test_insights_and_chat(client):
    ins = client.get("/api/insights")
    assert ins.status_code == 200
    body = ins.json()
    if body.get("stats", {}).get("today_energy", 0) > 0:
        assert "tou" in body
        assert "carbon_kg" in body
        assert "twin" in body
        showcase = body.get("showcase") or {}
        replay = showcase.get("replay") or []
        if replay:
            assert len(replay) >= 20
            assert "energy_so_far" in replay[0]
            assert "optimized_power" in replay[0]
            assert showcase.get("benchmark")
            assert showcase.get("optimized_curve")
    chat = client.post("/api/insights/chat", json={"question": "为什么我家耗电？"})
    assert chat.status_code == 200
    assert chat.json()["answer"]
    bench = client.post("/api/insights/chat", json={"question": "今天比近30日中位高吗？"})
    assert bench.status_code == 200
    assert bench.json()["answer"]
    guide = client.post("/api/insights/chat", json={"question": "怎么用这套系统？"})
    assert guide.status_code == 200
    assert "使用说明" in guide.json()["answer"]


def test_strategy_simulate(client):
    listed = client.get("/api/strategies")
    assert listed.status_code == 200
    ids = [item["id"] for item in listed.json()[:3]]
    res = client.post("/api/strategies/simulate", json={"strategy_ids": ids})
    assert res.status_code == 200
    body = res.json()
    if body["before_kwh"] > 0:
        assert body["after_kwh"] <= body["before_kwh"]
        assert body["saving_percent"] >= 0
        assert body["saving_cost"] >= 0
        assert "hourly" in body


def test_butler_can_control_devices(client):
    before = client.get("/api/devices")
    assert before.status_code == 200
    ac = next((d for d in before.json() if d["device_type"] == "air_conditioner"), None)
    cmd = client.post("/api/butler/command", json={"text": "把空调调到26度"})
    assert cmd.status_code == 200
    body = cmd.json()
    assert "拧到26" in body["speech"] or "26" in body["speech"]
    assert body["intent"] == "setpoint"
    if ac and ac["current_power"] > 0:
        after = next((d for d in body["devices"] if d["id"] == ac["id"]), None)
        assert after is not None
        assert after["setpoint"] == 26
        assert after["current_power"] <= ac["current_power"]
    reject = client.post("/api/butler/command", json={"text": "关掉冰箱"})
    assert reject.status_code == 200
    assert reject.json()["intent"] == "reject"
    help_res = client.post("/api/butler/command", json={"text": "你会干什么"})
    assert help_res.status_code == 200
    assert help_res.json()["skills"]
    how = client.post("/api/butler/command", json={"text": "使用说明"})
    assert how.status_code == 200
    assert how.json()["intent"] == "guide"
    guest = client.post("/api/butler/command", json={"text": "有客人"})
    assert guest.status_code == 200
    assert guest.json()["intent"] == "scene_guest"
    weather = client.post("/api/butler/command", json={"text": "外面热不热"})
    assert weather.status_code == 200
    pending = weather.json().get("pending_cmd") or ""
    if pending:
        nod = client.post("/api/butler/command", json={"text": "点头"})
        assert nod.status_code == 200
        assert nod.json()["intent"] in ("setpoint", "ac_pref", "scene_eco")
    fridge_only = client.post("/api/butler/command", json={"text": "只留冰箱"})
    assert fridge_only.status_code == 200
    fridge = next((d for d in fridge_only.json()["devices"] if d["device_type"] == "refrigerator"), None)
    if fridge:
        assert fridge["status"] != "关闭"
    brief = client.post("/api/butler/command", json={"text": "汇报一下"})
    assert brief.status_code == 200
    spoken = brief.json()["speech"]
    assert "瓦" in spoken
    assert " W" not in spoken
    assert "W。" not in spoken
    reset = client.post("/api/butler/command", json={"text": "恢复原样"})
    assert reset.status_code == 200
    assert reset.json()["scene"] == "日常"


def test_life_os(client):
    res = client.get("/api/life")
    assert res.status_code == 200
    body = res.json()
    if body.get("clock"):
        assert body["clock"]["period"] in ("peak", "flat", "valley")
        assert "minutes_left" in body["clock"]
        assert len(body.get("family") or []) == 4
        assert "nilm" in body
        assert body["rules"]
        assert body.get("missions")
        assert body.get("demand")
        assert "saving_yuan" in (body.get("shift") or {})
        assert body.get("standby")
        assert body.get("defense")
        key = body["rules"][0]["key"]
        toggled = client.post("/api/life/rules", json={"key": key, "armed": True})
        assert toggled.status_code == 200
        assert toggled.json()["clock"]
        booked = client.post("/api/life/schedule", json={"task": "valley_wash", "booked": True})
        assert booked.status_code == 200
        assert any(s["key"] == "valley_wash" and s["booked"] for s in booked.json()["schedule"])
        mission_key = body["missions"][0]["key"]
        done = client.post("/api/life/missions", json={"key": mission_key, "done": True, "execute": False})
        assert done.status_code == 200
        client.post("/api/life/missions", json={"key": mission_key, "done": False, "execute": False})
        comfort = client.post("/api/life/comfort", json={"mode": "eco", "execute": False})
        assert comfort.status_code == 200
        assert comfort.json()["comfort"]["mode"] == "eco"
        client.post("/api/life/comfort", json={"mode": "balanced", "execute": False})
        client.post("/api/life/schedule", json={"task": "valley_wash", "booked": False})
        client.post("/api/life/demand", json={"action": "reset"})
        chat = client.post("/api/insights/chat", json={"question": "有没有电网削峰邀约？"})
        assert chat.status_code == 200
        assert chat.json()["answer"]
        butler = client.post("/api/butler/command", json={"text": "今晚任务"})
        assert butler.status_code == 200
        assert butler.json()["speech"]


def test_source_map_and_ingest_contract(client):
    res = client.get("/api/sources")
    assert res.status_code == 200
    body = res.json()
    assert len(body.get("modalities") or []) == 4
    assert body.get("alignment", {}).get("percent", 0) >= 90
    assert "occupancy" in (body.get("forecast_features") or [])
    assert body.get("portability")
    dropped = client.get("/api/sources/degrade", params={"drop": "behavior"})
    assert dropped.status_code == 200
    deg = dropped.json()
    assert "occupancy" in (deg.get("lost_features") or [])
    ok = client.post("/api/sources/validate", json={
        "modality": "energy",
        "rows": [{"timestamp": "2026-08-19 20:30:00", "device_id": 1, "power": 100, "energy": 0.01}],
    })
    assert ok.status_code == 200
    assert ok.json()["ok"] is True
    assert ok.json()["would_write"] is False
    bad = client.post("/api/sources/validate", json={"modality": "energy", "rows": [{"timestamp": "2026-08-19 20:30:00"}]})
    assert bad.status_code == 200
    assert bad.json()["ok"] is False
    chat = client.post("/api/insights/chat", json={"question": "数据从哪来？能移植吗？"})
    assert chat.status_code == 200
    assert "四路" in chat.json()["answer"] or "多模态" in chat.json()["answer"]


def test_model_lab_and_honest_metrics(client):
    res = client.get("/api/models")
    assert res.status_code == 200
    body = res.json()
    assert body.get("honesty")
    forecast = body.get("forecast") or {}
    load = body.get("load") or {}
    anomaly = body.get("anomaly") or {}
    if forecast.get("metrics"):
        assert "R2" in forecast["metrics"]
        assert "MAPE" in forecast["metrics"]
        assert "accuracy" in forecast["metrics"]
    if load.get("available"):
        assert load.get("not_nilm") is True
        assert "不是" in (load.get("honesty") or "") or "NILM" in (load.get("honesty") or "")
    if anomaly.get("available"):
        assert anomaly.get("labeled") == 13
        assert anomaly.get("detected") == 27
        assert anomaly.get("f1") == 0.35
    insights = client.get("/api/insights")
    assert insights.status_code == 200
    radar = insights.json().get("radar") or {}
    if radar:
        assert "comfort" in radar
        assert radar.get("notes", {}).get("comfort")
    pred_chat = client.post("/api/insights/chat", json={"question": "预测准不准？"})
    assert pred_chat.status_code == 200
    assert "MAPE" in pred_chat.json()["answer"] or "R²" in pred_chat.json()["answer"] or "R2" in pred_chat.json()["answer"]
    nilm = client.post("/api/insights/chat", json={"question": "负荷识别是 NILM 吗？"})
    assert nilm.status_code == 200
    assert "NILM" in nilm.json()["answer"] or "盲拆" in nilm.json()["answer"] or "分路" in nilm.json()["answer"]
