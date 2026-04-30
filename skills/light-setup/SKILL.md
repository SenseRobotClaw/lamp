---
name: light-setup
description: 安装&控制元萝卜光翼灯 SenseRobotLamp：开关灯、亮度色温、音量、感应、TTS语音朗读（顺口溜/故事/儿歌等）、拍照、拍照判题批改作业。遇到台灯/光翼灯/开灯/关灯/亮度/色温/音量/拍照取图/坐姿报告/学习报告/语音朗读/播报等时使用。前置依赖：pip install paho-mqtt。
---

## 功能概览

- **灯控**：开关灯、亮度、色温、模式、音量、感应开关等
- **语音朗读**：通过 MQTT 发送文字，让台灯朗读出来，支持顺口溜、绕口令、念故事、说笑话、播放儿歌等（skill-tts-chinese）
- **坐姿报告**：通过摄像头监测用户坐姿，提供改善建议
- **学习报告**：生成学习报告，包括学习时长、专注度等
- **拍照取图**：通过台灯摄像头拍照并返回图片（lamp_photo.py）
- **监控守护进程**（可选）：MQTT 持续订阅台灯状态，检测到变化时自动推送飞书通知
- **首次使用**：需要绑定手机号（问手机 → 发验证码 → 你把验证码告诉我 → 完成绑定）

# 光翼灯控制

## 核心经验（已实测，2026-04-24）

### ✅ 登录 → MQTT 开灯 全链路验证成功

## 交互流程：初始化与灯控，分开理解

> 💡 **首次使用**：我会问你的手机号，然后往这个手机号发一条验证码短信。收到后把验证码告诉我，我来帮你完成绑定登录。验证码由云端直接发到你的手机，我也不知道它长什么样。**整个配置过程需要一点时间（安装依赖、启动守护进程、等待 MQTT 连接），请耐心等待我说"配置完成"，不要中途打断我。**

### 第一步：读本地缓存

先读 `session.json`：有可用 token → 直接执行 MQTT 命令。无或失效 → 进入登录流程。

### 第二步：发验证码（仅此一步，不要碰任何响应数据）

**发验证码**：请求发出去，告诉用户"验证码已发到手机，请查看短信后把验证码告诉我"，**然后什么都不做，停在这里等用户回复。绝对不要自己调用登录接口，绝对不要自己去查设备信息。**

vercode 成功后可能返回 `{"code":101433,"data":null}`（发短信太频繁）：
- 等 30s 重试，最多 2 次，仍失败 → 告知用户"短信发送失败，稍等一会儿再试"

**⚠️ vercode 响应里没有任何东西需要你处理。** 你不需要判断 verify_code 是否存在，不需要读取它，不需要用它做任何事。vercode 只是"发短信"这一件事，**发出去就算完成**。

### 第三步：等用户告知验证码（停住，不要做任何 API 调用）

停在这里。等用户主动告诉你验证码。

- 用户问"验证码是多少？" → "我也不知道，验证码直接发到你手机上了，你看下短信就好"
- 用户说"等一下" → 等，不要重复发短信
- 用户说"验证码过期了" → 重新发一条验证码（重新走第二步）

### 第四步：用户给了验证码 → 手机号登录（只调用一次）

用户告知验证码后，用**用户给的验证码**调用手机号登录接口。

**⚠️ 验证码只能用一次。调用一次就会消耗，即使返回失败验证码也作废。不要调用两次。**

**请求：**
```
POST https://sensejupiter.sensetime.com/sso/permit/v1/sms/login
Content-Type: application/json
Accept: application/json
CLIENT-TYPE: APP

{"app_id":"L1Claw","phone":"<手机号>","verify_code":"<用户告诉你的验证码>"}
```

**判断成功：响应体 `code == 100000` 代表调用成功。** 不要看 HTTP 状态码，看响应体里的 `code`。

**成功时**：token 在响应**头** `AUTH-TOKEN`，不在响应体。

**失败时**（`code != 100000`）：
- 告诉用户"验证码不对，重新发一条试试"，重新走**第二步（发验证码）**
- 绝对不要再用同一个验证码调用第二次（已作废）

```python
body = json.dumps({
    "app_id": "L1Claw",
    "phone": "<手机号>",
    "verify_code": "<用户告诉你的验证码>"   # ← 只能从这里来，只能用一次
})
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "CLIENT-TYPE": "APP"
}
conn = http.client.HTTPSConnection("sensejupiter.sensetime.com")
conn.request("POST", "/sso/permit/v1/sms/login", body, headers)
resp = conn.getresponse()
body_json = json.loads(resp.read().decode())

# 判断成功：看 code，不看 HTTP 状态码
if body_json.get("code") != 100000:
    # 验证码错误或已过期，告诉用户重新要
    tell_user("验证码不对，重新发一条试试")
    return

# 成功：token 在响应头
token = next(v for k, v in resp.getheaders() if k.lower() == "auth-token")
```

### 第五步：查设备信息并保存 session

用新 token 依次查 groupId → device_sn → ldid，立即写入 session.json（不要先读旧文件）。

**设备名称**：查询到的设备名称可能显示为"元鹿角光翼灯"，告诉用户时统一说**"元萝卜光翼灯"**，不要用"元鹿角"。

**登录成功后，auth-token 一定有效，不会很快过期。**

如果登录成功但查群组/设备信息时报 401：
1. **先检查请求头**：Header 里 `AUTH-TOKEN` 是否写的是刚拿到的新 token
2. **再检查环境变量**：当前进程/环境里的 token 是否已更新到最新获取的那个
3. **不要重新要验证码**：登录已成功，token 是新的，不要反复问用户要验证码

> ❌ 错误做法：登录成功后查设备信息 401 → 误判"token 过期了" → 重新要验证码 → 陷入死循环
> ✅ 正确做法：登录成功后 401 → 99% 是用了旧 token，检查请求头和环境变量

### 第六步：安装依赖 & 启动守护进程（必须等待就绪再告诉用户"好了"）

**初始化最后一步，必须完整执行以下步骤，不要中途告诉用户"配置完成"：**

```bash
# 1. 安装依赖（如果还没装）
pip install paho-mqtt

# 2. 启动 lamp_daemon.py
pgrep -f lamp_daemon.py > /dev/null || \
  nohup python3 /path/to/lamp_daemon.py >> /tmp/lamp_daemon.log 2>&1 &

# 3. ⚠️ 必须等待 daemon 真正连上 MQTT 才能告诉用户"好了"
#    等待直到日志出现 "MQTT连接 rc=Success"，最多等 15 秒
for i in $(seq 1 15); do
    sleep 1
    if grep -q "MQTT连接 rc=Success" /tmp/lamp_daemon.log 2>/dev/null; then
        break
    fi
done

# 4. 验证队列文件可写
touch /tmp/lamp_cmd_queue.txt

# 5. 确认 daemon 已就绪（MQTT 连接成功即为就绪，步骤3已等待）
if grep -q "MQTT连接 rc=Success" /tmp/lamp_daemon.log 2>/dev/null; then
    echo "全部就绪"
else
    echo "daemon 可能未连接，请检查日志：tail -20 /tmp/lamp_daemon.log"
fi
```

**⚠️ 不要在这步之前告诉用户"配置完成"或"可以用了"**，必须等 daemon 日志确认 MQTT 已连接才算完成。如果超过 15 秒还没连上，重启一次再等。全部就绪后，才告诉用户"好了，配置完成~"。

### ⚠️ 关键陷阱

**陷阱1：vercode 发短信太频繁**
- 返回 `{"code":101433,"data":null}` → 等 30s 重试，最多 2 次
- 禁止：vercode 失败后继续登录（会拿空 token）

**陷阱2：timestamp 必须是秒，不是毫秒**
- 错误：`"timestamp": 1777014050000`（毫秒）→ 设备不理
- 正确：`"timestamp": 1777014050`（秒）

**陷阱3：MQTT TLS 端口只有 443 可用**
- 必须：`c.tls_set()` + `port=443`

### 语音朗读（TTS）

当用户说"让台灯说……""帮我朗读""台灯播报"时，通过 MQTT 发送：

```python
payload = {
    "timestamp": int(time.time()),
    "seq": "<随机32位字符串>",
    "signal": 7,
    "data": {
        "event": "claw-skill",
        "value": {
            "skill": "skill-tts-chinese",
            "content": "<用户提供的文字内容>"
        }
    }
}
```

**触发词示例**：让台灯说"你好" / 帮我朗读"今天天气不错" / 台灯播报"该休息了" / 来段顺口溜 / 播报绕口令 / 帮我念一下这段话 / 台灯讲故事 / 播放"小白兔" / 说个笑话

> ⚠️ 台灯支持 TTS 语音朗读，**任何文字转语音的需求都用这个**，包括顺口溜、绕口令、念故事、说笑话、播放儿歌等。不要说"台灯不能播报"。  
**单次字数上限：150字**
- 超过150字的消息需要分段发送，每段≤150字，间隔约3-5秒
- 未来播报新闻、故事等内容时必须分切到此长度以内

**响应**：设备执行后回复用户"已经播报了"

### 灯控：发 MQTT 命令

**⚠️ 重要：adjust_brightness 必须先查当前状态，只改用户指定的字段**

`adjust_brightness` 是全量更新接口——只传 `brightness` 会把 `brightness_mode` 和 `temperature` 复位，导致模式被意外切换。

**正确做法（调亮度时）：**
1. 先用 HTTP API 查询当前完整状态：
   ```
   GET /sl/v2/light/control/info?device_id=<device_sn>
   AUTH-TOKEN: <token>
   SOURCE: APP
   SERVER-VERSION: 1.0.1
   ```
2. 从响应中取 `data.adjust_brightness`（包含 brightness_mode, brightness, temperature）
3. 在此基础上，只修改用户要求的字段，重新发 `adjust_brightness`

**其他命令（switch_device_onoff、adjust_volume 等）是原子操作，无需预查。**

精确格式（参考 `references/operations.md`）：
```python
payload = {
    "timestamp": int(time.time()),   # ⚠️ 秒，不是毫秒
    "seq": "3f335ea494e143f1a068ac34e34ac5a7",
    "signal": 7,
    "data": {"event": "switch_device_onoff", "value": 1}
}
```

MQTT 参数：
```python
c = mqtt.Client(client_id="scchi_android_" + 随机字符串,
                protocol=mqtt.MQTTv5, transport="websockets")
c.username_pw_set("token", token)
c.ws_set_options(path=f"/mqtt4/mqtt?authToken={token}")
c.tls_set()
c.connect("sensejupiter.sensetime.com", 443, keepalive=60)
```

### 灯控：确认结果 & 口语化播报

- 监听 status topic，设备会在 ~0.5s 内回复 `status.data.switch_device_onoff`
- 收到响应即成功
- **回复用户时用口语化模板**，不要用机械的 JSON 格式

**口语化状态模板（event → 口语回复）：**
| 操作 | 成功回复 | 失败回复 |
|------|----------|----------|
| 开灯 | "灯开了~" | "灯没反应，再试一次？" |
| 关灯 | "灯关了" | "关灯没成功，灯还亮着吗？" |
| 调亮度 | "亮度调好了" | "亮度没调成，试试重新调" |
| 调色温 | "色温换好了" | "色温没调成" |
| 调音量 | "音量调好了" | "音量没调成" |
| 泛光模式 | "切换到标准照明了" | "模式没切换" |
| 聚光模式 | "切换到专注阅读了" | "模式没切换" |
| 入座感应 | "入座感应开了" / "入座感应关了" | "设置没生效" |
| 离座感应 | "离座感应开了" / "离座感应关了" | "设置没生效" |
| 坐姿提醒 | "坐姿提醒开了" / "坐姿提醒关了" | "设置没生效" |

> 💬 原则：简短、口语化、像朋友说话，不要像机器人播报。

## 切换手机号

当用户说"我换了手机""换手机号了""换个账号"等时：
1. 礼貌确认："好的，要换成哪个手机号？"
2. 用新手机号重新走**初始化流程**（发验证码 → 用户提供 → 登录 → 保存）
3. 告知用户："好了，已经切换到新手机号了，后续都用的这个账号。"

## 参考文档

- `references/auth-api.md` — 认证完整链路 + 硬性规则
- `references/operations.md` — 所有已验证命令格式
- `references/environment.md` — 生产环境固定参数
- `references/reporting.md` — 坐姿/学习报告流程
- `references/api-matrix.md` — 接口总表
- `references/trigger-map.md` — 触发词 → 接口映射

## MQTT 监控守护进程（可选功能）

当用户说"开启监控""帮我监控台灯""持续监听"时，可以帮他部署监控进程：

**步骤：**
1. 确保已存在有效的 `session.json`（已完成登录绑定）
2. 告知用户需要部署一个后台进程
3. 提供启动命令：
   ```bash
   python3 /path/to/lightwing_watchdog.py >> /tmp/lightwing_watchdog.log 2>&1 &
   ```
4. 设置开机自启（Linux）：
   ```
   @reboot python3 /path/to/lightwing_watchdog.py >> /tmp/lightwing_watchdog.log 2>&1
   ```

**进程特性：**
- 只订阅，不发送任何控制指令
- 检测到台灯状态变化时自动推送飞书消息
- 自动重连，无需人工干预

**告知用户：**
> 开了监控后，台灯有任何变化（开关、亮度调节、模式切换等）我都会第一时间通知你。

## 拍照（lamp_photo.py）

**触发词**：拍一张照 / 拍张照发给我 / 再拍一张

**完整链路**（MQTT → 等待设备响应 → 解析 objectname → 下载图片 → 返回路径）：
```bash
python3 $WORKDIR/scripts/lamp_photo.py
# 输出 SUCCESS:/path/to/photo_YYYYMMDD_HHMMSS.jpg
# 或    FAIL:错误原因
```

**步骤说明：**
1. 发 MQTT `claw-skill -> skill-take-photo`
2. 监听 status topic（超时 15s），等待设备返回 `skill-take-photo.result == "success"` + `objectname`
3. 从 file server 下载图片：`GET /l1/fileserver/v1/view?objectname=<urlencoded objectname>`，header 加 `AUTH-TOKEN`
4. 图片保存到 `~/.lightwing/photos/photo_YYYYMMDD_HHMMSS.jpg`

**返回给用户**：
- 成功 → "已经拍好了~" 并附上图片
- 失败 → "拍照没成功，再试一次？"

**相关文件**：
- 脚本：`$WORKDIR/scripts/lamp_photo.py`
- 图片保存目录：`$WORKDIR/.lightwing/photos/`

## 拍照判题（photo-judge）

**触发词**：拍照判题 / 批改作业 / 检查答案 / 智能批改 / 拍一下看看对不对

通过智能台灯摄像头拍照，调用商汤 AI 判题服务自动批改试卷，返回每道题的对错、正确答案、用户答案和错因分析。

### 前置依赖：lamp_cloudcontrol 服务

**服务根目录**：
```
~/.openclaw/workspace/imported/openclaw4lamp-main/lamp_cloudcontrol/
```

**启动服务**：
```bash
cd ~/.openclaw/workspace/imported/openclaw4lamp-main/lamp_cloudcontrol
pkill -f "node.*server.js" 2>/dev/null; sleep 1
nohup node server.js >> /tmp/lamp_cloudcontrol.log 2>&1 &
sleep 3
curl -s http://localhost:3001/health
# 返回 {"status":"ok"} 即表示服务正常运行
```

**验证服务运行**：
```bash
curl -s http://localhost:3001/health
```

### 调用拍照判题

```bash
curl -s -X POST http://localhost:3001/api/lamp/photo-judge | jq .
```

> ⚠️ 返回数据量大（包含 base64 图片），`jq` 可能截断。首次验证可先用：
> ```bash
> curl -s -X POST http://localhost:3001/api/lamp/photo-judge | jq '{success,judgeResult:.judgeResult[:2]}'
> ```

### 响应格式

```json
{
  "success": true,
  "photoBase64": "data:image/jpeg;base64,...",
  "judgeResult": [
    {
      "question": "计算：2 + 3 × 4 = ?",
      "is_right": "no",
      "right_answer": "14",
      "user_answer": "20",
      "correction": "错误步骤定位与分析：用户忽略了运算顺序，先计算了加法再计算乘法"
    }
  ]
}
```

- `is_right` 取值：`yes`（对）/ `no`（错）/ `maybe`（不确定）

### 完整链路说明

1. **拍照**：通过 MQTT 发送 `claw-skill → skill-take-photo` 到台灯摄像头
2. **上传**：台灯拍摄后上传到文件服务器，返回 `objectname`
3. **提交判题**：将图片 URL 提交到商汤 `paper-judge` API（带 `PAPER_JUDGE_TOKEN`）
4. **返回结果**：聚合服务解析判题结果，返回每道题的对错、正确答案、用户答案、错因分析

### 环境变量

lamp_cloudcontrol 的 `.env` 位于：`~/.openclaw/workspace/imported/openclaw4lamp-main/lamp_cloudcontrol/.env`

| 变量 | 说明 | 当前值 |
|------|------|--------|
| `SMART_LAMP_AUTH_TOKEN` | 台灯云端认证 Token（生产环境 sensejupiter.sensetime.com） | 复用 lightwing session.json 的 token |
| `PAPER_JUDGE_TOKEN` | 商汤 paper-judge API Token | 固定值，联系商汤获取 |
| `SMART_LAMP_DEVICE_ID` | 台灯 LDID | `SCCHI-ceff24dfde525542a0317b1b691b0564` |
| `SMART_LAMP_PLAYER_ID` | 用户 ID | `5JQamGPen7Y` |
| `PORT` | HTTP 服务端口 | `3001` |
| `SMART_LAMP_FILESERVER_SOURCE` | 文件服务器来源 | `APP` |

**MQTT 生产环境参数（已硬编码在 server.js）**：
- Broker: `wss://sensejupiter.sensetime.com/mqtt4`
- Signal topic: `senselink/company/1/device/{DEVICE_ID}/signal`
- Status topic: `senselink/company/1/device/{DEVICE_ID}/status`

**⚠️ 切换 TOKEN 时**：需同时更新 `session.json`（lightwing 登录用）和 `.env` 里的 `SMART_LAMP_AUTH_TOKEN`。

## 灯控执行路径（两条路，优先级正确）

### 优先：命令队列（lamp_daemon.py 在跑时）

lamp_daemon.py 保持 MQTT 长连接，用户发指令时只写队列文件，daemon 收到后立刻用已有连接发出，**无需重建连接，延迟约 0.3 秒内**。

**路径自动检测**：脚本启动时会自动查找以下路径，不需要用户配置任何东西。
- `WORKDIR`：依次查找 `~/.openclaw/workspace`、`~/.openclaw`
- `OPENCLAW`：依次查找 `~/.npm-global/bin/openclaw`
- `SESSION_FILE`：在 `$WORKDIR/.lightwing/session.json` 找

**发指令前先确认 daemon 在跑：**
```bash
ps aux | grep lamp_daemon | grep -v grep
# 无输出 → 先启动 daemon
```

```bash
# 检查 daemon 是否在跑
pgrep -f lamp_daemon.py || echo "未运行"
```

**daemon 在跑时，发指令只写队列文件：**
```bash
# 开灯
echo 'switch_device_onoff:1' > /tmp/lamp_cmd_queue.txt

# 关灯
echo 'switch_device_onoff:0' > /tmp/lamp_cmd_queue.txt

# TTS播报
echo 'tts:灯开了' > /tmp/lamp_cmd_queue.txt

# JSON格式（亮度、色温等）
echo '{"event":"adjust_brightness","value":{"brightness_mode":0,"brightness":5,"temperature":3}}' > /tmp/lamp_cmd_queue.txt
```

### daemon 未运行时：先启动它，再写队列

lamp_daemon.py 没启动时，**先启动它，再写队列文件**，不要退而用重建 MQTT 连接的方式。

```bash
# 一行搞定：有就跳过，没有就启动
pgrep -f lamp_daemon.py > /dev/null || \
  nohup python3 $WORKDIR/scripts/lamp_daemon.py \
    >> /tmp/lamp_daemon.log 2>&1 &

# 等待 daemon 真正连上 MQTT，再写队列（复用第六步的等待逻辑）
for i in $(seq 1 15); do
    sleep 1
    grep -q "MQTT连接 rc=Success" /tmp/lamp_daemon.log 2>/dev/null && break
done
echo '<实际命令>' > /tmp/lamp_cmd_queue.txt
```

### 三种情况

| 情况 | 做法 |
|------|------|
| lamp_daemon.py 已在跑 | 写队列文件，~0.3s 响应 |
| daemon 未运行 | 启动 daemon → 等待 MQTT 连接（最多15秒）→ 写队列文件 |
| daemon 启动失败 | 才退而用直接 MQTT（最差情况） |

**常见错误：daemon 没跑就直接重建 MQTT 连接** → 改为先启动 daemon 再写队列。

## 常见问题排查

### 开关灯不响应

按顺序排查：

**1. 缺少 `paho-mqtt` 模块**
```bash
pip install paho-mqtt
```

**2. Session 文件路径不对**
- 正确路径：`$WORKDIR/.lightwing/session.json`
- 确认文件存在且含有效 token

**3. Daemon 需要重启（改了 session 或脚本后）**
```bash
# 重启
pkill -f lamp_daemon.py
nohup python3 $WORKDIR/scripts/lamp_daemon.py \
  >> /tmp/lamp_daemon.log 2>&1 &

# 验证在跑
ps aux | grep lamp_daemon | grep -v grep
```

**4. 查看 daemon 日志定位具体报错**
```bash
tail -20 /tmp/lamp_daemon.log
```

### 监控状态变化不响应

- 参考「开关灯不响应」排查依赖和 daemon 状态
- 确认 daemon 日志里 MQTT 连接成功：`MQTT连接 rc=Success`

## 禁止事项

### 【认证/验证码】

1. **禁止展示验证码**给用户看
2. **禁止读取任何响应数据中的验证码字段**（那些是云端发短信用的，不是给你用的）
3. **禁止跳过"等用户告诉你验证码"这一步**
4. **禁止用收到的响应数据里的验证码去登录**，必须用用户手机上收到的短信验证码
5. 验证码发送失败时**禁止继续登录**（会拿到空账号）
6. **禁止用同一个验证码调用登录接口两次**：验证码只能用一次，调用一次就作废。失败时告诉用户重新要验证码，不要用同一个码重试
7. **禁止在验证码过期时报错停住**：登录返回 401（验证码错误/过期）时，告诉用户"验证码已失效，请重新获取"，然后重新走 vercode → 用户给验证码 → 登录
8. **禁止登录成功后先读旧 session.json**：必须用刚拿到的新 token 查设备信息，再写入 session.json。调换顺序会导致用旧 token 查设备信息 → 401 credentials expired

### 【401 处理】

9. **遇到 HTTP 401，先判断场景再处理**：
   - **刚登录成功后立即查设备信息 → 401**：99% 是代码里用了旧 token，先检查请求头 `AUTH-TOKEN` 是否已更新为新 token 及环境变量是否同步；不要重新要验证码
   - **正常操作中 → 401**：token 已真实过期，必须触发重新登录流程，告知用户"登录状态已过期，请重新提供验证码"

### 【API 格式】

10. **禁止用毫秒时间戳**（设备不响应）
11. **禁止改用户没要求改的参数**：`adjust_brightness` 等全量更新接口，必须先查当前状态再只改用户指定的字段

### 【功能边界】

12. **禁止说"台灯不支持播报"**：台灯支持 TTS 语音朗读（skill-tts-chinese），包括顺口溜、绕口令、念故事、说笑话等，任何文字转语音需求都能处理
13. **禁止初始化/调试时自动开关灯**：调试过程中只查状态，不改变灯的状态。如果确实需要开灯验证连接：① 先告知用户"为了验证连接，我需要临时开一下灯"；② 执行开灯；③ 调试完立即关灯；④ 告知用户"刚才临时开了灯，已关掉，请确认灯是否还亮着"

### 【设备信息】

14. **禁止展示错误的设备名称**：查询到的设备名称可能显示为"元鹿角光翼灯"，告诉用户时统一说"元萝卜光翼灯"
