#!/usr/bin/env python3
"""
光翼灯 MQTT 监控守护进程
功能：
  - 持续订阅台灯状态 topic
  - 检测到状态变化时，自动通过飞书/消息推送通知用户
  - 不发送任何控制指令（只监不控）
安装：
  # 开机自启（Linux）
  @reboot python3 /path/to/lightwing_watchdog.py >> /tmp/lightwing_watchdog.log 2>&1
  # 或用 systemd 管理
配置：
  WORKDIR = 设置为 session.json 所在目录
  FEISHU_TARGET = 飞书用户 ID（可从 inbound_meta 获取）
  OPENCLAW = openclaw 可执行文件路径
"""

import paho.mqtt.client as mqtt
import json, time, os, threading, sys, re

# ── 路径自动检测（与 lamp_daemon.py 保持一致）──────────────────
_home = os.path.expanduser("~")
_wdir = os.environ.get("LIGHTWING_WORKDIR", "")
if not _wdir or not os.path.isdir(_wdir):
    for _d in [os.path.join(_home, ".openclaw", "workspace"),
               os.path.join(_home, ".openclaw")]:
        if os.path.isdir(_d):
            _wdir = _d
            break
WORKDIR       = _wdir
SESSION_FILE  = os.environ.get("LIGHTWING_SESSION",
                    os.path.join(WORKDIR, ".lightwing", "session.json"))
STATE_FILE    = "/tmp/lightwing_last_state.json"
LOG_FILE      = "/tmp/lightwing_watchdog.log"
OPENCLAW      = os.environ.get("LIGHTWING_OPENCLAW", os.path.join(_home, ".npm-global", "bin", "openclaw"))
FEISHU_TARGET = os.environ.get("LIGHTWING_FEISHU_TARGET", "ou_bf4314b08df70c2b95f2c2b33ac1f4ce")
# ──────────────────────────────────────────────────────────────

sess      = None
mqtt_cli  = None
log_lock  = threading.Lock()
last_state = None

def log(msg):
    ts = time.strftime("%H:%M:%S")
    with log_lock:
        with open(LOG_FILE, "a") as f:
            f.write(f"[{ts}] {msg}\n")
        print(f"[{ts}] {msg}", flush=True)

def load_sess():
    with open(SESSION_FILE) as f:
        return json.load(f)

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return None

def save_state(d):
    with open(STATE_FILE, "w") as f:
        json.dump(d, f)

def get_fields(d):
    adj = d.get("adjust_brightness", {})
    return {
        "onoff":  d.get("switch_device_onoff"),
        "bright": adj.get("brightness"),
        "temp":   adj.get("temperature"),
        "mode":   adj.get("brightness_mode"),
        "auto":   d.get("switch_auto_brightness"),
    }

def fmt_status(d):
    f = get_fields(d)
    on   = "开" if f["onoff"] == 1 else "关" if f["onoff"] == 0 else f"未知({f['onoff']})"
    mode = "聚光" if f["mode"] == 1 else "泛光" if f["mode"] == 0 else ""
    return f"灯={on} | 亮度={f['bright']}/5 | 色温={f['temp']}/5 {mode}"

def meaningful(old, new):
    """判断状态是否有实质变化"""
    if old is None: return True
    return get_fields(old) != get_fields(new)

def push_feishu(text):
    """通过 openclaw 发送飞书消息"""
    esc = text.replace('"', '\\"')
    os.system(f'{OPENCLAW} message send --channel feishu --target {FEISHU_TARGET} --message "{esc}" > /dev/null 2>&1')

def on_connect(client, userdata, flags, rc, properties=None):
    global last_state
    if rc == 0:
        log("✅ MQTT连接成功")
        client.subscribe(sess["status_topic"], qos=1)
        last_state = load_state()
        log(f"已订阅: {sess['status_topic']}")
    else:
        log(f"❌ MQTT连接失败 rc={rc}")

def on_disconnect(client, userdata, reasonCode, properties=None):
    log(f"⚠️ 断开连接 rc={reasonCode}")

def on_message(client, userdata, msg):
    global last_state
    try:
        data = json.loads(msg.payload.decode())
        d = data.get("data", {})

        # 只处理含灯光状态的消息（开关灯或亮度/色温变化）
        if "switch_device_onoff" not in d and "adjust_brightness" not in d:
            return

        changed = meaningful(last_state, d)
        status_str = fmt_status(d)

        if changed:
            now = time.strftime("%H:%M")
            msg_text = f"📡 [{now}] 台灯状态变化\n{status_str}"
            push_feishu(msg_text)
            log(f"[变化] {status_str}")
        else:
            log(f"[未变] {status_str}")

        last_state = d.copy()
        save_state(d)

    except Exception as e:
        log(f"[解析错误] {e}")

def main():
    global sess, mqtt_cli

    # 检查 session
    if not os.path.exists(SESSION_FILE):
        log(f"❌ 未找到 session.json，请先完成登录绑定: {SESSION_FILE}")
        sys.exit(1)

    sess = load_sess()
    log(f"[启动] 设备={sess.get('device_sn', '?')} ldid={sess.get('ldid', '?')}")

    # 随机 client_id 避免重复
    import random, string
    cid = "lw_watchdog_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

    c = mqtt.Client(
        client_id=cid,
        protocol=mqtt.MQTTv5,
        transport="websockets",
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )
    c.username_pw_set("token", sess["token"])
    c.ws_set_options(path=f"/mqtt4/mqtt?authToken={sess['token']}")
    c.tls_set()
    c.on_connect    = on_connect
    c.on_disconnect = on_disconnect
    c.on_message   = on_message
    mqtt_cli = c

    delay = 3
    while True:
        try:
            log("[连接中...]")
            c.connect("sensejupiter.sensetime.com", 443, keepalive=60)
            c.loop_forever()
        except Exception as e:
            log(f"[异常] {e}，{delay}s后重连")
            time.sleep(delay)
            delay = min(delay * 2, 60)

if __name__ == "__main__":
    main()
