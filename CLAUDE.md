# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

This is the **元萝卜（YuanLuoBo）光翼灯/龙虾灯 OpenClaw Skills** framework — a collection of Claude Code skills for controlling the SenseRobot Lamp via MQTT. Skills are deployed to `~/.openclaw/skills/` on the user's machine.

## Skill Architecture

Each skill is a directory under `skills/` with a `SKILL.md` (the skill definition Claude reads and executes) and optionally a `scripts/` directory with Python helpers.

**Install order is mandatory**: `ylb-lamp-setup` must be installed first. All other skills depend on it for session, daemon, and scripts.

```
skills/
├── ylb-lamp-setup/       ← Core: auth, MQTT daemon, lamp_photo.py
├── ylb-lamp-test/        ← Smoke test (12 lamp operations)
├── ylb-lamp-mind-breath/ ← 2-minute mindfulness breathing scene
└── ylb-lamp-elsa-story/  ← Elsa bilingual story scene
```

**Shared runtime paths** (not in git, created at runtime):
```bash
SHARED=~/.openclaw/skills/.ylb-lamp
SESSION=$SHARED/session.json       # auth token + device info
SCRIPTS=~/.openclaw/skills/ylb-lamp-setup/scripts
CMD_FILE=/tmp/lamp_cmd_queue.txt   # command queue
LOG=/tmp/lamp_daemon.log
PHOTOS=/tmp/lamp_photos/
```

## Naming Convention

All skills use the `ylb-lamp-` prefix. New application skills follow: `ylb-lamp-<feature>`.

## Key Architecture: Command Queue + Daemon

The core execution pattern is a **persistent MQTT daemon** (`lamp_daemon.py`) that holds the WebSocket/TLS connection to the broker, and all skills write to a **queue file** (`/tmp/lamp_cmd_queue.txt`) rather than opening their own MQTT connections.

- Daemon in running → write to queue file → ~0.3s response
- Daemon not running → start daemon, wait for `"MQTT连接 rc=Success"` in log (up to 15s), then write queue
- Never bypass the daemon with a direct MQTT connection unless daemon fails to start

**Queue file format:**
```bash
# Simple commands
echo 'switch_device_onoff:1' > /tmp/lamp_cmd_queue.txt
echo 'tts:想说的文字' > /tmp/lamp_cmd_queue.txt

# JSON for brightness/temperature (must include all three fields)
echo '{"event":"adjust_brightness","value":{"brightness_mode":0,"brightness":3,"temperature":2}}' > /tmp/lamp_cmd_queue.txt
```

## MQTT Connection Parameters

```python
host = "sensejupiter.sensetime.com"
port = 443          # only port that works
protocol = MQTTv5
transport = "websockets"
path = f"/mqtt4/mqtt?authToken={token}"
tls_set()           # must enable TLS
username_pw_set("token", token)
client_id = "scchi_android_" + random_string
```

**Topics:**
- Send: `senselink/company/1/device/<ldid>/signal`
- Receive: `senselink/company/1/device/<ldid>/status`

## MQTT Payload Format

```python
{
    "timestamp": int(time.time()),   # MUST be seconds, not milliseconds
    "seq": "<random 32-char hex>",
    "signal": 7,
    "data": {"event": "<event_name>", "value": <value>}
}
```

## Critical Rules When Modifying Skills

1. **`adjust_brightness` is a full-update API** — always query current state first (`GET /sl/v2/light/control/info?device_id=<device_sn>`), then merge only the changed field. Sending partial data resets the other fields.

2. **Timestamp must be seconds** (`int(time.time())`), never milliseconds.

3. **TTS limit is 150 characters per message** — split longer content into chunks with ~3–5s delay between sends.

4. **`brightness_mode` switching causes audible hardware chime** — applications that switch modes frequently should mute volume at start (`adjust_volume: 0`) and restore after.

5. **Environment variable prefix is `YLBLAMP_`** (not `LIGHTWING_` — that was the old prefix, fully replaced).

6. **Device name**: always display as "元萝卜光翼灯", never "元鹿角光翼灯" (that's what the API may return).

## Running the Scripts

```bash
# Smoke test
python3 skills/ylb-lamp-test/scripts/lamp_smoke_test.py

# Start daemon manually
nohup python3 ~/.openclaw/skills/ylb-lamp-setup/scripts/lamp_daemon.py \
  >> /tmp/lamp_daemon.log 2>&1 &

# Check daemon status
pgrep -f lamp_daemon.py || echo "not running"
tail -20 /tmp/lamp_daemon.log

# Take a photo
python3 ~/.openclaw/skills/ylb-lamp-setup/scripts/lamp_photo.py
# Returns: SUCCESS:/tmp/lamp_photos/photo_YYYYMMDD_HHMMSS.jpg
```

## Reference Documents (in `ylb-lamp-setup/references/`)

| File | Contents |
|------|----------|
| `auth-api.md` | Full auth chain + hard rules |
| `operations.md` | All verified MQTT command formats |
| `environment.md` | Fixed production env params (host, port, headers) |
| `reporting.md` | Posture/study report API flow |
| `api-matrix.md` | All API endpoints summary |
| `trigger-map.md` | Trigger phrase → API mapping |
