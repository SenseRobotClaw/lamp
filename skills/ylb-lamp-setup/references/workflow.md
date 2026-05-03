# 工作流（简化版）

## 收到用户指令后

### 情况A：已有可用 session
1. 读 `session.json`
2. **如果是调亮度（adjust_brightness）**：先用 HTTP API 查当前状态，再只改用户指定的字段
3. **检查 daemon 在跑？** 是 → 写队列文件 `/tmp/lamp_cmd_queue.txt`；否 → 启动 lamp_daemon.py，等待 MQTT 连接（最多15秒）后再写队列
4. 等待 status 响应
5. 用口语化模板回复用户

### 情况B：无 session 或需要切换手机号
1. 问手机号
2. 用手机号调用 vercode（发短信到手机）
3. **不要打印验证码**，让用户告诉我收到的验证码
4. 用户提供验证码 → login → 从响应头取 token
5. token → 查 groupId → device_sn → ldid
6. 保存 session.json
7. **优先写队列文件**（lamp_daemon.py 在跑时）；daemon 未运行则先启动 daemon、等待 MQTT 连接，再写队列
8. 用口语化模板回复用户

### 情况C：vercode 获取失败（网络/接口问题）
1. 等 30s 重试
2. 再等 30s 重试
3. 仍失败 → 告知用户"短信发送失败了，稍等一会儿再试，或者联系工作人员"
4. **禁止**跳过继续登录（会拿空 token）

## 切换手机号

当用户说"换了手机""换手机号"时：
1. "好的，要换成哪个手机号？"
2. 获得新手机号后，执行清理：
   ```bash
   pkill -f lamp_daemon.py          # 停止 daemon，避免用旧 token 继续操作
   rm -f $SESSION                   # 删除登录凭证
   rm -f /tmp/lamp_cmd_queue.txt    # 清空指令队列
   rm -rf /tmp/lamp_photos/         # 清除临时照片
   ```
3. 拿到新手机号 → vercode → 用户给验证码 → 登录 → 保存 session.json
4. "好了，已经切换到新手机号了~"

## 开灯示例（完整 Python）

```python
import paho.mqtt.client as mqtt, json, time, uuid, urllib.request

# 1. 读 session
d = json.load(open(os.path.expanduser("~/.openclaw/skills/.ylb-lamp/session.json")))  # $SESSION
token = d["token"]
st = d["signal_topic"]
sst = d["status_topic"]

# 2. MQTT
msgs = []
def on_connect(c, u, flags, rc, p=None):
    if rc == 0:
        c.subscribe(sst, qos=1)
        c.publish(st, json.dumps({
            "timestamp": int(time.time()),  # ⚠️ 秒！
            "seq": "3f335ea494e143f1a068ac34e34ac5a7",
            "signal": 7,
            "data": {"event": "switch_device_onoff", "value": 1}
        }), qos=1)

def on_message(c, u, msg):
    dd = json.loads(msg.payload.decode())
    if dd["data"].get("switch_device_onoff") == 1:
        print("灯开了！")

def on_pub(c, u, mid, p=None):
    import threading
    threading.Thread(target=lambda: (time.sleep(6), c.disconnect())).start()

c = mqtt.Client(client_id="scchi_android_"+uuid.uuid4().hex[:8],
                protocol=mqtt.MQTTv5, transport="websockets")
c.username_pw_set("token", token)
c.ws_set_options(path=f"/mqtt4/mqtt?authToken={token}")
c.tls_set()
c.on_connect = on_connect
c.on_message = on_message
c.on_publish = on_pub
c.connect("sensejupiter.sensetime.com", 443, keepalive=60)
c.loop_start()
```

## 口语化回复模板

| 指令 | 成功回复 | 失败回复 |
|------|----------|----------|
| 开灯 | "灯开了~" | "灯没反应，再试一次？" |
| 关灯 | "灯关了" | "关灯没成功，灯还亮着吗？" |
| 调亮度 | "亮度调好了" | "亮度没调成，试试重新调" |
| 调色温 | "色温换好了" | "色温没调成" |
| 调音量 | "音量调好了" | "音量没调成" |
| 泛光模式 | "切换到标准照明了" | "模式没切换" |
| 聚光模式 | "切换到专注阅读了" | "模式没切换" |
| 入座感应 | "入座感应开了/关了" | "设置没生效" |
| 坐姿提醒 | "坐姿提醒开了/关了" | "设置没生效" |

> 💬 原则：简短、口语化、自然。像是朋友回复，不是机器人播报。
