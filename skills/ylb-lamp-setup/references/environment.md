# 环境（仅生产环境，已验证）

## API 基础
- `https://sensejupiter.sensetime.com`

## MQTT Broker（已验证可用）
- **Host:** `sensejupiter.sensetime.com`
- **Port:** `443`（唯一可用端口，其他均不通）
- **Protocol:** WebSocket + TLS
- **Path:** `/mqtt4/mqtt?authToken=<token>`
- **MQTT Version:** MQTTv5
- **TLS:** 必须开启

## Topic
- `senselink/company/1/device/<ldid>/signal`（发送命令）
- `senselink/company/1/device/<ldid>/status`（接收设备状态）

## HTTP Headers
```
AUTH-TOKEN: <token>
SOURCE: APP
SERVER-VERSION: 1.0.1
Content-Type: application/json
```

## Session 缓存路径
`~/.openclaw/skills/.ylb-lamp/session.json`（即 `$SESSION`，所有 ylb-lamp Skill 共用）
