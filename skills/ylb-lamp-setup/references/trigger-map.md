# 触发词 / 调用条件 / 返回解释

> 目的：让新接手的 agent 不只"知道有接口"，而是能根据用户一句话快速选对接口，并把结果解释成人话。

## 1. 开关灯

### 触发词
- 开灯
- 关灯
- 把灯打开
- 把台灯关掉

### 调用条件
- 默认按生产环境执行
- 已有可用 token / ldid / signal topic
- 优先走 MQTT `switch_device_onoff`

### 接口 / 事件
- MQTT event: `switch_device_onoff`

### 返回如何解释
- 若 `status.data.switch_device_onoff == 1`：回复"已经打开了"
- 若 `status.data.switch_device_onoff == 0`：回复"已经关掉了"
- 若只有 PUBACK 没有状态确认：回复"指令已经发出，但还没收到设备状态确认"

---

## 2. 亮度 / 色温 / 模式

### 触发词
- 调亮一点 / 调暗一点
- 亮度调到最亮
- 色温调暖一点 / 调冷一点
- 切到专注阅读模式
- 切到标准照明模式

### 调用条件
- 灯已开更稳；若效果异常，可先开灯再重试
- 亮度 / 色温用 `adjust_brightness` 完整对象
- 色温解释优先基于泛光模式

### 接口 / 事件
- MQTT event: `adjust_brightness`

### 返回如何解释（MQTT 链路）
- 看 `status.data.adjust_brightness`
- 若亮度值变化成功：回复"已经帮你调亮/调暗了"
- 若模式变为 `brightness_mode=1`：回复"已经切到专注阅读模式"
- 若模式变为 `brightness_mode=0`：回复"已经切到标准照明模式"
- 若温度值达到边界：回复"已经调到当前可用范围的较暖/较冷一档"

---

## 3. 音量

### 触发词
- 音量调大一点
- 音量调小一点
- 静音一点

### 调用条件
- 已有可用 MQTT 连接

### 接口 / 事件
- MQTT event: `adjust_volume`

### 返回如何解释
- 看 `status.data.adjust_volume`
- 若值更新成功：回复"已经帮你调整音量了"

---

## 4. 自适应光源

### 触发词
- 自适应光源打开
- 自动亮度打开
- 自动亮度关闭

### 调用条件
- 已有可用 MQTT 连接

### 接口 / 事件
- MQTT event: `switch_auto_brightness`

### 返回如何解释
- 若 `status.data.switch_auto_brightness == 1`：回复"自适应光源已经打开"
- 若 `status.data.switch_auto_brightness == 0`：回复"自适应光源已经关闭"

---

## 5. 按键背光

### 触发词
- 按键背光打开
- 按键背光关掉

### 调用条件
- 已有可用 MQTT 连接

### 接口 / 事件
- MQTT event: `switch_button_backlight`

### 返回如何解释
- 若 `status.data.switch_button_backlight == 1`：回复"按键背光已经打开"
- 若 `status.data.switch_button_backlight == 0`：回复"按键背光已经关闭"

---

## 6. 入座 / 离座感应

### 触发词
- 入座感应打开 / 关闭
- 离座感应打开 / 关闭
- 入座离座提醒关掉

### 调用条件
- 已有可用 MQTT 连接
- 需要按对象同时传 `leaving_detect` / `seating_detect`

### 接口 / 事件
- MQTT event: `switch_auto_sense`

### 返回如何解释
- 看 `status.data.switch_auto_sense`
- 若 `seating_detect` 变化：解释为"入座感应已更新"
- 若 `leaving_detect` 变化：解释为"离座感应已更新"
- 两者都改了：解释为"入座和离座感应都已更新"

---

## 7. 聚光追踪

### 触发词
- 聚光追踪打开
- 聚光追踪关闭
- 跟随打开

### 调用条件
- 已有可用 MQTT 连接

### 接口 / 事件
- MQTT event: `adjust_spotlight_tracking`

### 返回如何解释
- 看 `status.data.adjust_spotlight_tracking.switch`
- 若为 `1`：回复"聚光追踪已经打开"
- 若为 `0`：回复"聚光追踪已经关闭"

---

## 8. 中文播报 / 语音朗读（TTS）

### 触发词（任何一条匹配即触发）
- 说：让台灯说"你好" / 台灯说一句话 / 帮我说话
- 播放：播放"你好" / 帮我播放 / 播放这个
- 播报：帮我播报 / 台灯播报 / 播报一下
- 朗读：帮我朗读 / 朗读这段 / 朗读出来
- 顺口溜：来段顺口溜 / 播报顺口溜 / 台灯说个顺口溜
- 绕口令：来段绕口令 / 台灯说绕口令 / 播报绕口令
- 念：帮我念一下 / 念出来 / 帮我念
- 讲故事：讲个故事 / 台灯讲故事

> ⚠️ 台灯支持 TTS 语音朗读功能，**不是"不能播报"。**只要是文字转语音的需求，都用 skill-tts-chinese 处理。

### 调用条件
- 已有可用 MQTT 连接
- 文本内容由用户明确提供（或用户让台灯自己选）

### 接口 / 事件
- MQTT `claw-skill -> skill-tts-chinese`

### 返回如何解释
- 若 `status.data.skill-tts-chinese.result == success`：回复"已经播报了"
- 若无明确成功字段：回复"播报指令已经发出，请留意设备侧反馈"

---

## 9. 拍照

### 触发词
- 拍一张照
- 拍张照发给我
- 再拍一张并存下来

### 完整链路（lamp_photo.py，已实测）

推荐直接调用脚本，完整链路如下：

```bash
python3 $SCRIPTS/lamp_photo.py
# 输出：SUCCESS:/tmp/lamp_photos/photo_YYYYMMDD_HHMMSS.jpg
# 或：  FAIL:错误原因
```

**链路步骤：**
1. 发 MQTT 拍照指令 `claw-skill -> skill-take-photo`
2. 监听 status topic，等待设备回包（超时 15s）
3. 解析 `status.data["skill-take-photo"]`，提取 `objectname`
4. 从 file server 下载图片：`GET /l1/fileserver/v1/view?objectname=<urlencoded objectname>`
5. 图片保存到 `/tmp/lamp_photos/photo_YYYYMMDD_HHMMSS.jpg`

**返回如何解释：**
- `SUCCESS:...` → 图片已就绪，回复用户"已经拍好了"
- `FAIL:...` → 拍照失败，回复用户"拍照没成功，再试一次？"

**手动链路（无脚本时）：**
1. 发 MQTT `claw-skill -> skill-take-photo`
2. 收到 `status.data["skill-take-photo"].result == "success"` + `objectname`
3. `GET /l1/fileserver/v1/view?objectname=<urlencoded objectname>`，header 加 `AUTH-TOKEN`
4. 图片二进制保存本地，返回给用户

---

## 10. 灯控状态补查

### 触发词
- 看看灯现在是什么状态
- 现在亮度是多少
- 查一下当前灯控状态

### 调用条件
- 用户要的是"查状态"，不是"修改状态"
- 已有 device_sn 和 token

### 接口 / 事件
- `GET /sl/v2/light/control/info?device_id=<device_sn>`

### 返回如何解释（HTTP API）
- 成功判定：`code == 100000`
- 把原始字段转成自然语言：
  - 当前是否开灯
  - 当前模式
  - 当前亮度
  - 当前色温
  - 是否开启自适应光源等
- 不要直接把接口 JSON 原样甩给用户，除非用户明确要求

---

## 11. 设备信息 / ldid 查询

### 触发词
- 查设备信息
- 查 ldid
- 看这台灯的设备状态

### 调用条件
- 已有 `device_sn`
- 常用于初始化、排障、补查设备信息

### 接口 / 事件
- `GET /sl/v2/facade/devices/info?duid=<device_sn>`

### 返回如何解释（HTTP API）
- 成功判定：`code == 100000`（注意不是 `success` 字段）
- 如果目标是初始化：提取 `ldid` 供后续 MQTT 使用
- 如果目标是排障：解释为"我查到了设备基础信息/在线状态/版本信息"
- 不要误用旧的 v2 usercenter facade 接口

---

## 12. 今天 / 某一天坐姿检测报告

### 触发词
- 看今天的坐姿检测报告
- 今天坐姿怎么样
- 给我一份今天的学习报告

### 调用条件
- 先走 `groupId -> playerId` 链路
- 传当天 00:00 的毫秒时间戳

### 接口 / 事件
- `GET /l1/usercenter/v1/groups/user?roleType=1&isAll=false`
- `GET /l1/usercenter/v1/players?groupId=<groupId>`
- `GET /l1/usercenter/v1/players/<playerId>/posture/record?date=<timestamp>`

### 返回如何解释
- 优先看：`todayPerformance` / `fatigueDetail` / `detailRecords`
- 如果用户要的是“学习报告”，优先按 `references/reporting.md` 里的“微信报告”模板输出
- 输出风格：更口语化、更像家长通知、先鼓励再总结
- 若记录为空：回复"今天暂时还没有足够的数据生成完整报告"
- 不要把"没拿到真实 playerId"解释成"没有报告"

---

## 13. 最近七天学习 / 坐姿报告

### 触发词
- 最近七天坐姿报告
- 最近一周学习表现
- 过去七天怎么样

### 调用条件
- 先走 `groupId -> playerId` 链路

### 接口 / 事件
- `GET /l1/usercenter/v1/groups/user?roleType=1&isAll=false`
- `GET /l1/usercenter/v1/players?groupId=<groupId>`
- `GET /l1/usercenter/v1/players/<playerId>/posture/record/last_seven_days`

### 返回如何解释
- 输出成趋势总结：
  - 近七天整体趋势
  - 相对稳定的时段或表现
  - 需要改善的习惯
  - 建议关注点
- 语气保持温和，不用生硬诊断口吻

---

## 14. 姿态实景开关

### 触发词
- 看一下实景开关状态
- 把姿态实景打开 / 关闭

### 调用条件
- 先走 `groupId -> playerId` 链路
- 用户明确要求查看或调整实景开关

### 接口 / 事件
- `GET /l1/usercenter/v1/players/<playerId>/posture/switch/real_scene`
- `POST /l1/usercenter/v1/players/<playerId>/posture/switch/real_scene`

### 返回如何解释
- GET：解释为"当前实景开关状态"
- POST：解释为"已经帮你打开/关闭姿态实景"

---

## 15. 版本检查

### 触发词
- 查一下版本
- 看看 app 版本检查结果
- 现在版本链路正常吗

### 调用条件
- 用户明确要做版本检查或排障

### 接口 / 事件
- `POST /sl/ota/v2/app/check-version`

### 返回如何解释
- 解释为"版本检查接口可用 / 返回了版本信息"
- 如果只是排障，不要把这一步说成灯控本身失败或成功

---

## 16. 验证码登录

### 触发词
- 初始化
- 重新登录
- 重新连接
- 换 token

### 调用条件
- 本地没有可用 token，或 token 已失效
- 需要走短信登录链路

### 接口 / 事件
- `POST /sso/permit/v1/vercode`
- `POST /sso/permit/v1/sms/login`

### 返回如何解释
- vercode 成功后，告诉用户"已往你手机发验证码了，收到后把验证码告诉我"
- **绝对禁止**把 vercode 响应里的字段拿出来用于登录
- 如果登录成功并拿到响应头里的 `AUTH-TOKEN`：解释为"已经完成登录/连接恢复"
- 如果登录返回 401（验证码错误/过期）：告诉用户"验证码已失效，请重新获取"，重新走 vercode → 用户给验证码 → 登录

---

## 17. 明确不要用的接口

### 触发词
- 当 agent 想当然去查 devices info 旧路径时

### 调用条件
- 只要看到旧接口，就应主动避开

### 接口 / 事件
- 不要使用：`GET /l1/usercenter/v2/facade/devices/info?duid=<device_sn>`

### 返回如何解释
- 不对用户强调"我本来想用错接口"
- 直接切换到正确接口并继续执行
