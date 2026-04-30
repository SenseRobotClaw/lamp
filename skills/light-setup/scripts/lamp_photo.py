#!/usr/bin/env python3
"""
光翼灯拍照完整链路
1. 发 MQTT 拍照指令（claw-skill -> skill-take-photo）
2. 监听 status topic，等待设备回包
3. 解析 objectname
4. 从 file server 下载图片二进制
5. 保存到本地并打印路径（供 agent 返回给用户）

环境变量（可覆盖）：
  LIGHTWING_WORKDIR  工作目录（默认: ~/.openclaw/workspace 或 ~/.openclaw）
  LIGHTWING_SESSION  session.json 路径
  LIGHTWING_PHOTOS   图片保存目录
"""
import os, sys, time, random, string, json
import urllib.request, urllib.parse
import paho.mqtt.client as mqtt

# ── 路径自动检测 ────────────────────────────────────────────
home = os.path.expanduser("~")
wdir = os.environ.get("LIGHTWING_WORKDIR", "")
if not wdir or not os.path.isdir(wdir):
    for d in [os.path.join(home, ".openclaw", "workspace"),
                os.path.join(home, ".openclaw")]:
        if os.path.isdir(d):
            wdir = d
            break
WORKDIR     = wdir
SESSION_FILE = os.environ.get("LIGHTWING_SESSION",
                    os.path.join(WORKDIR, ".lightwing", "session.json"))
SAVE_DIR    = os.environ.get("LIGHTWING_PHOTOS",
                    os.path.join(WORKDIR, ".lightwing", "photos"))
LOG_FILE    = "/tmp/lamp_photo.log"
TIMEOUT     = 15   # 秒

def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"[{ts}] {msg}\n")
    except: pass

def load_sess():
    if not os.path.exists(SESSION_FILE):
        raise FileNotFoundError(f"session.json 未找到: {SESSION_FILE}")
    return json.load(open(SESSION_FILE))

def download_image(token, objectname, save_path):
    url = (f"https://sensejupiter.sensetime.com/l1/fileserver/v1/view"
           f"?objectname={urllib.parse.quote(objectname)}")
    req = urllib.request.Request(url, headers={
        "AUTH-TOKEN": token,
        "SOURCE": "APP",
        "SERVER-VERSION": "1.0.1",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read()
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(data)
        log(f"下载完成: {len(data)} bytes → {save_path}")
        return save_path

def main():
    os.makedirs(SAVE_DIR, exist_ok=True)
    sess = load_sess()
    token = sess["token"]
    signal_topic = sess["signal_topic"]
    status_topic = signal_topic.replace("/signal", "/status")
    log(f"拍照开始 device_sn={sess.get('device_sn','?')}")

    result = {"done": False, "success": False, "objectname": None, "error": None}

    def on_connect(client, userdata, flags, rc, props=None):
        if rc != 0:
            result["error"] = f"MQTT连接失败 rc={rc}"
            result["done"] = True
            log(f"MQTT连接失败 rc={rc}")
            return
        client.subscribe(status_topic, qos=1)
        client.publish(signal_topic, json.dumps({
            "timestamp": int(time.time()),
            "seq": ''.join(random.choices(string.ascii_lowercase + string.digits, k=32)),
            "signal": 7,
            "data": {"event": "claw-skill", "value": {"skill": "skill-take-photo"}}
        }), qos=1)
        log("拍照指令已发送")

    def on_message(client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
        except:
            return
        skill_data = data.get("data", {}).get("skill-take-photo", {})
        if not skill_data:
            return
        rc = skill_data.get("result")
        log(f"设备响应: result={rc}, data={skill_data}")
        if rc == "success":
            result["objectname"] = skill_data.get("objectname")
            result["success"] = True
        else:
            result["error"] = f"设备拍照失败: {rc}"
        result["done"] = True

    cid = "scchi_photo_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    c = mqtt.Client(
        client_id=cid,
        protocol=mqtt.MQTTv5,
        transport="websockets",
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )
    c.username_pw_set("token", token)
    c.ws_set_options(path=f"/mqtt4/mqtt?authToken={token}")
    c.tls_set()
    c.on_connect = on_connect
    c.on_message = on_message
    c.connect("sensejupiter.sensetime.com", 443, keepalive=60)
    c.loop_start()

    waited = 0
    while not result["done"] and waited < TIMEOUT:
        time.sleep(0.5)
        waited += 0.5

    c.disconnect()
    c.loop_stop()

    if not result["success"] or not result["objectname"]:
        err = result.get("error") or "未获取到 objectname"
        log(f"失败: {err}")
        print(f"FAIL:{err}", flush=True)
        sys.exit(1)

    ts = time.strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(SAVE_DIR, f"photo_{ts}.jpg")
    try:
        download_image(token, result["objectname"], save_path)
        print(f"SUCCESS:{save_path}", flush=True)
    except Exception as e:
        log(f"下载失败: {e}")
        print(f"FAIL:下载图片失败 {e}", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
