#!/usr/bin/env python3
"""
光翼灯常驻守护进程
- 持续保持MQTT连接
- 监听命令文件 /tmp/lamp_cmd_queue.txt，有命令立即发送
- 监听设备状态变化，即时推送飞书
- 通过文件与主进程通信，实现快速响应

环境变量（可覆盖）：
  YLBLAMP_SESSION    session.json 路径（默认: ~/.openclaw/skills/.ylb-lamp/session.json）
  YLBLAMP_LOG        日志文件（默认: /tmp/lamp_daemon.log）
  YLBLAMP_FEISHU_TARGET  飞书推送目标用户ID
"""
import paho.mqtt.client as mqtt
import json, time, random, string, os, threading, subprocess

# ── 路径约定 ──────────────────────────────────────────────────
def find_path():
    """解析 SHARED / OPENCLAW / SESSION_FILE 路径"""
    home = os.path.expanduser("~")
    shared = os.path.join(home, ".openclaw", "skills", ".ylb-lamp")

    # OPENCLAW
    openclaw = os.environ.get("YLBLAMP_OPENCLAW", "")
    if not openclaw or not os.path.isfile(openclaw):
        for p in [os.path.join(home, ".npm-global", "bin", "openclaw"),
                   "/usr/local/bin/openclaw"]:
            if os.path.isfile(p):
                openclaw = p
                break

    sess_path = os.environ.get("YLBLAMP_SESSION",
                    os.path.join(shared, "session.json"))

    return shared, sess_path, openclaw

SHARED, SESSION_FILE, OPENCLAW = find_path()

STATE_FILE     = "/tmp/lamp_last_state.json"
CMD_FILE       = "/tmp/lamp_cmd_queue.txt"
LOG_FILE       = os.environ.get("YLBLAMP_LOG", "/tmp/lamp_daemon.log")
FEISHU_TARGET  = os.environ.get("YLBLAMP_FEISHU_TARGET", "")

sess       = None
mqtt_cli   = None
log_lock   = threading.Lock()
last_state = None
last_cmd   = None

def log(msg):
    ts = time.strftime("%H:%M:%S")
    with log_lock:
        with open(LOG_FILE, "a") as f:
            f.write(f"[{ts}] {msg}\n")

def load_sess():
    with open(SESSION_FILE) as f:
        return json.load(f)

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except: return None

def save_state(d):
    with open(STATE_FILE, "w") as f:
        json.dump(d, f)

def get_fields(d):
    adj = d.get("adjust_brightness", {})
    return {
        "onoff":  d.get("switch_device_onoff"),
        "bright": adj.get("brightness"),
        "temp":   adj.get("temperature"),
        "auto":   d.get("switch_auto_brightness"),
    }

def fmt_status(d):
    f = get_fields(d)
    on   = "开" if f["onoff"]==1 else "关" if f["onoff"]==0 else f"?({f['onoff']})"
    auto = "⚙️自适应" if f["auto"]==1 else ""
    return f"灯={on} | 亮度={f['bright']}/5 | 色温={f['temp']}/5  {auto}"

def meaningful(old, new):
    if old is None: return True
    return get_fields(old) != get_fields(new)

def push_feishu(text):
    if not FEISHU_TARGET or not OPENCLAW:
        log(f"[飞书] 未配置 YLBLAMP_FEISHU_TARGET 或 OPENCLAW，跳过推送")
        return
    esc = text.replace('"', '\\"')
    os.system(f'{OPENCLAW} message send --channel feishu --target {FEISHU_TARGET} --message "{esc}" > /dev/null 2>&1')

def mqtt_send(event, value=None, skill_val=None):
    global last_cmd
    # switch_device_onoff 永远不跳过（用户操作必须执行）
    key = f"{event}:{json.dumps(value) if value is not None else 'null'}"
    if key == last_cmd and event != "switch_device_onoff":
        log(f"[跳过重复] {event}")
        return
    last_cmd = key

    data = {"event": event}
    if skill_val is not None:
        data["value"] = skill_val
    elif value is not None:
        data["value"] = value

    payload = {
        "timestamp": int(time.time()),
        "seq": ''.join(random.choices(string.ascii_lowercase + string.digits, k=32)),
        "signal": 7,
        "data": data
    }
    if mqtt_cli is None or not mqtt_cli.is_connected():
        log(f"[MQTT] 未连接，跳过: {event}")
        return
    mqtt_cli.publish(sess["signal_topic"], json.dumps(payload), qos=1)
    log(f"[MQTT] {event} = {value if value is not None else skill_val}")

def process_cmd_file():
    try:
        if not os.path.exists(CMD_FILE): return
        with open(CMD_FILE) as f:
            content = f.read().strip()
        if not content: return
        with open(CMD_FILE, "w") as f: f.write("")

        if content.startswith("tts:"):
            text = content[4:]
            log(f"[命令] TTS: {text[:30]}...")
            mqtt_send("claw-skill", skill_val={"skill":"skill-tts-chinese","content":text})
        elif content.startswith("{"):
            try:
                cmd_data = json.loads(content)
                mqtt_send(cmd_data["event"], value=cmd_data.get("value"))
            except Exception as e:
                log(f"[命令解析失败] {e}: {content}")
        else:
            parts = content.split(":", 1)
            if len(parts) >= 2:
                event, val_str = parts
                try:
                    val = json.loads(val_str)
                except:
                    try:    val = int(val_str)
                    except: val = val_str
                log(f"[命令] {event} = {val}")
                mqtt_send(event, value=val)
    except Exception as e:
        log(f"[cmd错误] {e}")

def on_connect(client, userdata, flags, rc, properties=None):
    global last_state
    log(f"MQTT连接 rc={rc}")
    client.subscribe(sess["status_topic"], qos=1)
    # 只订阅状态，不主动发任何控制指令（只监不控）
    last_state = load_state()

def on_message(client, userdata, msg):
    global last_state
    try:
        data = json.loads(msg.payload.decode())
        d = data.get("data", {})

        # 设备状态包至少有 switch_device_onoff 或 adjust_brightness
        # 只要有一个就处理，不要静默丢弃物理开关/App直接操作的消息
        if "switch_device_onoff" not in d and "adjust_brightness" not in d:
            log(f"[忽略] 非状态消息: {list(d.keys())}")
            return

        changed = meaningful(last_state, d)
        status_str = fmt_status(d)

        if changed:
            now = time.strftime("%H:%M")
            msg_text = f"[{now}] 📡 台灯状态变化\n{status_str}"
            push_feishu(msg_text)
            log(f"[状态变化] {status_str}")
        else:
            log(f"[状态未变] {status_str}")

        last_state = d.copy()
        save_state(d)
    except Exception as e:
        log(f"[msg错误] {e}")

def main():
    global sess, mqtt_cli
    sess = load_sess()
    log(f"[启动] 设备={sess.get('device_sn', '?')}")

    cid = "scchi_daemon_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    c = mqtt.Client(client_id=cid, protocol=mqtt.MQTTv5, transport="websockets",
                    callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    c.username_pw_set("token", sess["token"])
    c.ws_set_options(path=f"/mqtt4/mqtt?authToken={sess['token']}")
    c.tls_set()
    c.on_connect = on_connect
    c.on_message = on_message
    mqtt_cli = c   # ⚠️ 必须在 cmd_watcher 启动前赋值，否则线程读到 None 直接报错

    def cmd_watcher():
        while True:
            process_cmd_file()
            time.sleep(0.3)
    threading.Thread(target=cmd_watcher, daemon=True).start()

    delay = 3
    while True:
        try:
            log("[连接MQTT...]")
            c.connect("sensejupiter.sensetime.com", 443, keepalive=60)
            c.loop_forever()
        except Exception as e:
            log(f"[异常] {e}，{delay}s后重连")
            time.sleep(delay)
            delay = min(delay * 2, 60)

if __name__ == "__main__":
    main()
