---
name: lamp-smoke-test
description: 元萝卜光翼灯/龙虾灯（SenseRobotLamp）冒烟测试脚本，用于快速遍历台灯所有功能并验证是否正常工作。触发场景：用户说"冒烟测试"、"跑一遍灯的功能"、"测试台灯所有功能"、"快速测试灯"、或要求打包灯功能测试脚本时使用。
---

# 光翼灯冒烟测试

## 功能描述

自动遍历光翼台灯全部功能，每项操作前通过 TTS 语音提示即将测试的内容，执行完成后语音播报结果。

## 前置检查

```bash
SHARED=~/.openclaw/skills/.ylb-lamp
SESSION=$SHARED/session.json
SCRIPTS=~/.openclaw/skills/ylb-lamp-setup/scripts

# 检查 session 是否存在
if [ ! -f "$SESSION" ]; then
    echo "❌ session.json 不存在，请先运行 ylb-lamp-setup 完成登录"
    exit 1
fi

# 检查 daemon 是否在跑，没跑就启动
pgrep -f lamp_daemon.py > /dev/null || {
    nohup python3 $SCRIPTS/lamp_daemon.py >> /tmp/lamp_daemon.log 2>&1 &
    for i in $(seq 1 15); do
        sleep 1
        grep -q "MQTT连接 rc=Success" /tmp/lamp_daemon.log 2>/dev/null && break
    done
}
```

## 使用方式

```bash
python3 scripts/lamp_smoke_test.py
```

## 测试流程（共12项）

| 步骤 | 操作 | TTS 提示（执行前） | TTS 提示（执行后） |
|------|------|-------------------|------------------|
| 1 | 开灯 | "即将进行开灯测试，请注意" | "开灯测试成功" |
| 2 | 音量→最大 | "即将测试音量调节，先调到最大" | "音量已调到最大" |
| 3 | 音量→最小 | "即将测试音量调节，调到最小" | "音量已调到最小" |
| 4 | 聚光模式 | "即将测试聚光模式，切换到专注阅读" | "已切换到专注阅读模式" |
| 5 | 亮度→最大 | "即将测试亮度调节，调到最大" | "亮度已调到最大" |
| 6 | 亮度→最小 | "即将测试亮度调节，调到最小" | "亮度已调到最小" |
| 7 | 标准照明 | "即将切换到标准照明模式" | "已切换到标准照明模式" |
| 8 | 亮度→最大 | "即将测试亮度调节，调到最大" | "亮度已调到最大" |
| 9 | 亮度→最小 | "即将测试亮度调节，调到最小" | "亮度已调到最小" |
| 10 | 色温→最冷 | "即将测试色温调节，调到最冷" | "色温已调到最冷" |
| 11 | 色温→最暖 | "即将测试色温调节，调到最暖" | "色温已调到最暖" |
| 12 | 关灯 | "即将进行关灯测试，请注意" | "关灯测试成功" |

## 命令发送机制

脚本通过写队列文件 `/tmp/lamp_cmd_queue.txt` 发送指令，由 `lamp_daemon.py` 监听并通过 MQTT 发送到台灯。

## 依赖

- `$SCRIPTS/lamp_daemon.py` 必须在运行中（MQTT 长连接守护进程）
- TTS 语音提示在每项操作前后自动发送