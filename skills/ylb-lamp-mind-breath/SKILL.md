---
name: ylb-lamp-mind-breath
description: 2分钟正念呼吸 — 专为元萝卜光翼灯设计，触发口令"龙虾灯，打开2分钟正念呼吸"。泛光+暖色+偏暗柔和灯光，2分钟呼吸引导+语音提示，适合家长/成人使用。遇到：正念、呼吸练习、放松、2分钟正念时使用。前置依赖：lamp_daemon.py 在跑（MQTT长连接守护进程）。
---

# 龙虾灯专用 · 2分钟正念呼吸

## 技能概述

| 项目 | 内容 |
|------|------|
| 技能名称 | 2分钟正念呼吸 |
| 触发口令 | 龙虾灯，打开2分钟正念呼吸 |
| 总时长 | 120 秒（2分钟） |
| 适合人群 | 家长/成人 |

## 灯光规则

全程保持：**泛光 + 暖色 + 偏暗柔和**
- `brightness_mode: 0`（泛光）
- `temperature: 4`（最暖）
- `brightness: 1`（偏暗柔和）

## 正念时间轴

| 时间 | 内容 | 灯光 |
|------|------|------|
| 0:00 | 欢迎来到龙虾灯2分钟正念呼吸。请找一个舒服的姿势，轻轻闭上眼睛。 | 泛光+暖色+柔和 |
| 0:20 | 现在，我们慢慢吸气。用鼻子吸气，心里数4秒：一、二、三、四。 | 保持 |
| 0:30 | 慢慢呼气，数4秒：一、二、三、四。 | 保持 |
| 0:40 | 继续这样呼吸。吸气，放松身体。呼气，放下所有疲惫。 | 保持 |
| 1:00 | 把注意力只放在呼吸上。念头飘走也没关系，轻轻拉回来就好。 | 保持 |
| 1:20 | 继续安静呼吸。感受这一刻，只属于你自己的平静。 | 保持 |
| 1:40 | 最后20秒，保持自然、平稳的呼吸。 | 保持 |
| 1:55 | 准备慢慢回到现实。轻轻活动手指和肩膀。 | 保持 |
| 2:00 | 2分钟正念练习完成。愿你平静、轻松、充满力量。 | 保持 |

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
SKILL_SCRIPTS=~/.openclaw/skills/ylb-lamp-mind-breath/scripts
python3 $SKILL_SCRIPTS/mind_breath.py
```

## 命令发送机制

脚本通过写队列文件 `/tmp/lamp_cmd_queue.txt` 发送指令，由 `lamp_daemon.py` 监听并通过 MQTT 发送到台灯。

## 依赖

- `$SCRIPTS/lamp_daemon.py` 必须在运行中（MQTT 长连接守护进程）
- 队列文件 `/tmp/lamp_cmd_queue.txt` 可写
- TTS 语音在每个呼吸节拍时自动发送