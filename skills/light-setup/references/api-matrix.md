# 接口总表（已验证 / 应集成）

## 1. 认证与环境初始化

### 测试环境
- `POST /sso/permit/v1/vercode`
- `POST /sso/permit/v1/sms/login`
- `GET /sl/v2/facade/devices/info?duid=<device_sn>`

### 生产环境
- `POST /sso/permit/v1/vercode`
- `POST /sso/permit/v1/sms/login`
- `GET /sl/v2/facade/devices/info?duid=<device_sn>`

用途：
- 获取验证码
- 获取 `AUTH-TOKEN`
- 获取真实 `ldid`

## 2. MQTT 控制链路

### 主题
- `senselink/company/1/device/<ldid>/signal`
- `senselink/company/1/device/<ldid>/status`
- `senselink/company/1/device/<ldid>/alive`

### 已确认可用的控制能力
- 开关灯
- 亮度 / 色温 / 模式
- 音量
- 自适应光源
- 按键背光
- 入座 / 离座感应
- 聚光追踪
- 中文 TTS 播报
- 拍照

## 3. 灯状态与设备信息补查

### 灯控状态
- `GET /sl/v2/light/control/info?device_id=<device_sn>`

用途：
- MQTT 控制后做补确认
- 查询当前灯控状态

### 设备信息
- `GET /sl/v2/facade/devices/info?duid=<device_sn>`

用途：
- 查 `ldid`
- 查设备版本 / 在线状态等基础信息

## 4. 坐姿检测 / 学习报告

### 前置链路
- `GET /l1/usercenter/v1/groups/user?roleType=1&isAll=false`
- `GET /l1/usercenter/v1/players?groupId=<groupId>`

用途：
- 先拿真实 `groupId`
- 再拿真实 `playerId`

### 报告接口
- `GET /l1/usercenter/v1/players/<playerId>/posture/record?date=<当天00:00毫秒时间戳>`
- `GET /l1/usercenter/v1/players/<playerId>/posture/record/last_seven_days`

用途：
- 查询今天 / 某一天的坐姿检测报告
- 查询最近七天报告

### 实景开关
- `GET /l1/usercenter/v1/players/<playerId>/posture/switch/real_scene`
- `POST /l1/usercenter/v1/players/<playerId>/posture/switch/real_scene`

用途：
- 查询 / 调整姿态实景相关开关

## 5. 拍照取图

### 设备侧拍照
- MQTT `claw-skill -> skill-take-photo`

### 图片预览拉取
- `GET /l1/fileserver/v1/view?objectname=<urlencoded objectname>`

用途：
- 获取拍照后的 JPEG 图像

## 6. 版本检查

- `POST /sl/ota/v2/app/check-version`

用途：
- 查询 app / 控制链路版本检查信息

## 7. 明确不要依赖的接口

- `GET /l1/usercenter/v2/facade/devices/info?duid=<device_sn>`

原因：
- 生产环境已确认返回 `404 page not found`
- 不要把它当成稳定能力

## 8. skill 集成要求

1. 以上接口要作为统一能力面纳入 skill，不要只保留灯控。
2. 需要在 workflow 中明确：
   - 灯控类走 MQTT
   - 坐姿报告类先拿 `groupId` 再拿 `playerId`
   - 拍照类走 `skill-take-photo -> preview`
3. 面向用户输出时，优先给自然语言结果，不要直接甩接口路径。
4. 对高风险或删除类接口，不默认执行；需用户明确授权。
