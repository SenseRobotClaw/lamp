# 认证流程（生产环境，已验证）

## ⚠️ 最最重要的安全规则

验证码登录分两个完全不同的步骤：
1. **你发请求** → 云端往用户手机发短信 → 你收到一个响应（这个响应里有验证码字段）
2. **用户把手机上收到的验证码告诉你** → 你用这个去登录

> **绝对禁止：把第一步响应里的验证码拿出来登录。**
> 你唯一能用的验证码，是用户手机上收到的短信，由用户主动告诉你。

## Step 1：让云端发短信（只判断，不读取验证码）

```python
resp = requests.post("https://sensejupiter.sensetime.com/sso/permit/v1/vercode",
    json={"app_id":"LIGHT_APP","phone":"<手机号>"},
    headers={"Content-Type":"application/json","Accept":"application/json"}
)
data = resp.json()

# ⚠️ 只判断短信是否发出去了，绝对不读取响应里的验证码字段用于后续任何操作
if data.get("code") == 101433:  # 发短信太频繁（实测观察到的唯一具体错误码）
    time.sleep(30)  # 重试，最多2次
    resp = requests.post(...)
    data = resp.json()
    if data.get("code") == 101433: time.sleep(30); resp = requests.post(...); data = resp.json()
    if data.get("code") == 101433: 告知用户"短信发送失败，稍等一会儿再试"，停止; return
elif not data.get("data"):  # 其他非预期失败（不依赖具体 code 值）
    告知用户"短信发送失败，稍等一会儿再试"，停止
    return  # 禁止继续！
```

> 这一步完成后，你**不知道验证码是什么**，这是正常的。

## Step 2：等用户告诉你验证码

告诉用户："已往你的手机发了验证码，收到后把验证码告诉我（有效期约60秒，请尽快使用）。"

用户可能会问："验证码是多少？"
→ 答："我也不知道，验证码直接发到你手机上了，你看一下短信就好了。"

用户可能会说"等一下"或没回复
→ 等用户主动告诉你验证码，不要重复发短信。

**验证码过期处理**：如果用户说"验证码过期了""收不到"或登录返回 401，告诉用户"验证码已失效，我重新发一条"，重新走 Step 1。**绝对不要**让用户重复输入同一个已过期的验证码。

## Step 3：用用户提供的验证码登录（⚠️ 绝不能用 Step 1 响应里的验证码）

```python
# 验证码来源只有一种：用户手机上收到的短信，用户主动告诉你的
# 绝对不能用代码里任何响应数据中的验证码字段
body = json.dumps({
    "app_id": "LIGHT_APP",
    "phone": "<手机号>",
    "verify_code": "<用户手机上收到的短信验证码>"   # ← 只有这一种来源
})
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "CLIENT-TYPE": "APP"
}
conn = http.client.HTTPSConnection("sensejupiter.sensetime.com")
conn.request("POST", "/sso/permit/v1/sms/login", body, headers)
resp = conn.getresponse()
# 凭证在响应头，不在响应体
token = next(v for k,v in resp.getheaders() if k.lower() == "auth-token")
```

## Step 4：获取设备信息

```python
h = {"AUTH-TOKEN": token, "SOURCE": "APP", "SERVER-VERSION": "1.0.1"}

# 查 groupId
conn.request("GET", "/l1/usercenter/v1/groups/user?roleType=1&isAll=false", "", h)
groupId = json.loads(conn.getresponse().read().decode())["data"]["list"][0]["groupId"]

# 查 device_sn
conn.request("GET", f"/l1/usercenter/v1/devices?groupId={groupId}", "", h)
device_sn = json.loads(conn.getresponse().read().decode())["data"]["list"][0]["deviceId"]

# 查 ldid
conn.request("GET", f"/sl/v2/facade/devices/info?duid={device_sn}", "", h)
ldid = json.loads(conn.getresponse().read().decode())["data"]["ldid"]
```

## Step 5：保存 session

```python
import time
session = {
    "env": "prod",
    "base_url": "https://sensejupiter.sensetime.com",
    "phone": "<手机号>",
    "device_sn": device_sn,
    "token": token,
    "ldid": ldid,
    "signal_topic": f"senselink/company/1/device/{ldid}/signal",
    "status_topic": f"senselink/company/1/device/{ldid}/status",
    "alive_topic": f"senselink/company/1/device/{ldid}/alive",
    "mqtt_url": f"wss://sensejupiter.sensetime.com/mqtt4/mqtt?authToken={token}",
    "initialized_at": int(time.time())
}
with open(os.path.expanduser("~/.openclaw/workspace/.lightwing/session.json"), "w") as f:  # $WORKDIR 运行时自动检测
    json.dump(session, f, indent=2)
```

## Session 文件安全规则

**⚠️ 登录成功后，必须用刚拿到的 token 覆盖写入 session.json，不要读旧文件。**

常见出错模式（新龙虾特别容易踩）：
1. 本机已有旧的 `session.json`（含过期 token）
2. 登录成功后**先读了旧 session.json**（拿到旧 token），再用旧 token 查设备信息 → 401 credentials expired
3. 旧 token 写入 session.json，覆盖了刚拿到的新 token

**正确顺序（禁止调换）：**
```
登录 → 拿到新token → 立即查设备信息（用新token）→ 立即写入session.json（用新token）
```

**绝对禁止**：登录成功后先读旧 session.json，再用旧 token 去查设备信息。

## 常见错误处理

| 情况 | 原因 | 处理 |
|------|------|------|
| vercode 返回 null | 发短信太频繁 | 等 30s 重试，最多 2 次 |
| 登录返回空凭证 | 用错了验证码来源 | 确认用的是用户手机短信里的验证码 |
| 登录 401/验证码错误 | 验证码输错或已过期 | 告诉用户"验证码已失效，请重新获取"，重新走 vercode → 用户给验证码 → 登录 |
| HTTP API 401（正常操作中） | token 过期 | 重新走登录流程，告诉用户"登录状态已过期，请重新提供验证码" |
| HTTP API 401（刚登录后查设备） | 代码用了旧 token | 先检查请求头 AUTH-TOKEN 是否已更新为新 token，不要重新要验证码 |
| MQTT 连接失败 | 凭证过期 | 重新走登录流程 |

## 禁止清单

```
❌ 把 vercode 响应里的验证码字段拿出来用于登录
❌ 把任何验证码展示给用户
❌ 跳过"等用户告诉你验证码"这一步
❌ 跳过 vercode 成功判断直接登录
```
