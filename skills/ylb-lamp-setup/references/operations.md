# MQTT 操作格式（已验证，2026-04-24）

## ⚠️ 关键：timestamp 必须是秒，不是毫秒

```python
# ✅ 正确（秒）
timestamp = int(time.time())

# ❌ 错误（毫秒，设备不响应）
timestamp = int(time.time() * 1000)
```

## MQTT 连接参数（生产环境，已验证）

```python
import paho.mqtt.client as mqtt, json, time, uuid

# 连接
c = mqtt.Client(
    client_id="scchi_android_" + uuid.uuid4().hex[:8],  # 随机后缀
    protocol=mqtt.MQTTv5,
    transport="websockets"
)
c.username_pw_set("token", token)
c.ws_set_options(path=f"/mqtt4/mqtt?authToken={token}")
c.tls_set()
c.connect("sensejupiter.sensetime.com", 443, keepalive=60)
c.loop_start()

# 监听
def on_message(c, userdata, msg):
    status = json.loads(msg.payload.decode())
    # 设备在 ~0.5s 内回复
    # status["data"]["switch_device_onoff"] == 1 表示开
```

## 通用 Payload 格式

```json
{
  "timestamp": <int(秒时间戳)>,
  "seq": "3f335ea494e143f1a068ac34e34ac5a7",
  "signal": 7,
  "data": {
    "event": "<事件名>",
    "value": "<值>"
  }
}
```

## 已验证命令

### 1. 开关灯
```json
{"event":"switch_device_onoff","value":1}   // 开
{"event":"switch_device_onoff","value":0}   // 关
```

### 2. 亮度/色温/模式（完整对象）
```json
{
  "event": "adjust_brightness",
  "value": {
    "brightness_mode": 0,    // 0=泛光, 1=聚光
    "brightness": 5,         // 1-5 ， 亮度调节
    "temperature": 4          // 1-4，色温调节仅在泛光模式有效
  }
}
```

> ⚠️ **adjust_brightness 是全量更新接口**：只传 `brightness` 会把其他字段复位！
> **必须先通过 HTTP API 查询当前完整状态，再只修改用户指定的字段。**

### 3. 音量
```json
{"event":"adjust_volume","value":1}   // 1=最小 ， ？是最大 
```

### 4. 自适应光源
```json
{"event":"switch_auto_brightness","value":1}  // 开
{"event":"switch_auto_brightness","value":0}  // 关
```

### 5. 按键背光
```json
{"event":"switch_button_backlight","value":0}  // 关
{"event":"switch_button_backlight","value":1}  // 开
```

### 6. 入座/离座感应
```json
{
  "event": "switch_auto_sense",
  "value": {
    "leaving_detect": 0,   // 离座
    "seating_detect": 0    // 入座
  }
}
```

### 7. 聚光追踪
```json
{
  "event": "adjust_spotlight_tracking",
  "value": {
    "switch": 1,
    "adjust_moto_direction": 0,
    "adjust_moto_step": 0
  }
}
```

### 8. TTS 播报
```json
{
  "event": "claw-skill",
  "value": {
    "skill": "skill-tts-chinese",
    "content": "你好"
  }
}
```

### 9. 拍照
```json
{
  "event": "claw-skill",
  "value": {
    "skill": "skill-take-photo"
  }
}
```


## 状态确认

设备响应出现在 `status_topic`：
```python
status = json.loads(msg.payload.decode())
# status["data"]["switch_device_onoff"]  # 1=开，0=关
```

## 设备状态查询（HTTP 备用）
```
GET https://sensejupiter.sensetime.com/sl/v2/light/control/info?device_id=<device_sn>
AUTH-TOKEN: <token>
SOURCE: APP
SERVER-VERSION: 1.0.1
```
