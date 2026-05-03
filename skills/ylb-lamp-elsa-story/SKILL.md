---
name: elsa-bilingual-story
description: 艾莎公主1分钟双语故事 — 专为元萝卜光翼灯设计，触发口令"龙虾灯，我要听艾莎双语故事"。中英双语朗读配合灯光场景联动（泛光/聚光+冷暖色+亮度时序），约60秒，适合小学三年级。遇到：艾莎双语故事、龙虾灯、我要听艾莎双语故事、讲个双语故事时使用。前置依赖：lamp_daemon.py 在跑（MQTT长连接守护进程）。
---

# 艾莎公主1分钟双语故事

## 技能概述

| 项目 | 内容 |
|------|------|
| 技能名称 | 艾莎公主1分钟双语故事 |
| 触发口令 | 龙虾灯，我要听艾莎双语故事 |
| 总时长 | 约 60 秒 |
| 适合年龄 | 小学三年级 |

## 灯光规则

| 参数 | 值 | 说明 |
|------|------|------|
| `brightness_mode: 0` | 泛光 | 环境照明（冰雪场景） |
| `brightness_mode: 1` | 聚光 | 专注阅读（故事重点） |
| `temperature: 1` | 最冷 | 冰雪感，艾莎主题 |
| `temperature: 4` | 最暖 | 温馨感，励志段落 |
| `brightness: 1~5` | 亮度 | 按段落调整 |

## 故事时间轴

| 时间 | 中文 | 英文 | 灯光配置 |
|------|------|------|----------|
| 0:00–0:08 | 在遥远的北方，有一座冰雪城堡。 | In the far north, there is an ice castle. | 泛光 + 冷色 + 中等亮度 |
| 0:08–0:18 | 艾莎公主有冰雪魔法。 | Princess Elsa has ice magic. | 聚光 + 冷色 + 稍亮 |
| 0:18–0:28 | 雪花在空中轻轻飞舞。 | Snowflakes fly in the sky. | 泛光 + 冷色 + 稍暗 |
| 0:28–0:40 | 最强大的魔法，是善良与勇敢。 | The strongest magic is kindness and bravery. | 泛光 + 暖色 + 中等亮度 |
| 0:40–0:52 | 相信自己，你就是最棒的小公主。 | Believe in yourself. You are a great princess. | 聚光 + 暖色 + 柔和亮 |
| 0:52–1:00 | 艾莎的故事讲完啦，下次再见。 | See you next time. | 泛光 + 暖色 + 渐暗 |

## 前置检查
**路径约定**：所有 ylb-lamp Skill 共用的session & scripts 目录
```bash
SHARED=~/.openclaw/skills/.ylb-lamp
SESSION=$SHARED/session.json
SCRIPTS=~/.openclaw/skills/ylb-lamp-setup/scripts

[ -f "$SESSION" ] || { echo "❌ 请先运行 ylb-lamp-setup 完成登录"; exit 1; }

pgrep -f lamp_daemon.py > /dev/null || {
    nohup python3 $SCRIPTS/lamp_daemon.py >> /tmp/lamp_daemon.log 2>&1 &
    for i in $(seq 1 15); do
        sleep 1
        grep -q "MQTT连接 rc=Success" /tmp/lamp_daemon.log 2>/dev/null && break
    done
}
```

## 执行方式

```bash
SKILL_SCRIPTS=~/.openclaw/skills/ylb-lamp-elsa-story/scripts
python3 $SKILL_SCRIPTS/elsa_story.py
```

## 命令发送机制

脚本通过写队列文件 `/tmp/lamp_cmd_queue.txt` 发送指令，由 `lamp_daemon.py` 监听并通过 MQTT 发送到台灯。

## 依赖

- `$SCRIPTS/lamp_daemon.py` 必须在运行中（MQTT 长连接守护进程）
- 队列文件 `/tmp/lamp_cmd_queue.txt` 可写
- TTS 语音在每段故事朗读时自动发送

## 已知问题

- 台灯 MQTT 会话断开后可能出现命令不响应，需重新上电重置连接
- 建议定期重启 lamp_daemon.py 保持连接活跃
- 故事灯光在泛光/聚光之间多次切换，台灯每次切换时会发出语音播报；若需避免此声音，可手动在光翼灯上静音，或在脚本开头静音（`adjust_volume: 0？`）， TTS 朗读不要静音，需权衡
