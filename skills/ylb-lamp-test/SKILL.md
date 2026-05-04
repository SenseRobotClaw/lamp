---
name: ylb-lamp-test
description: 测试元萝卜龙虾灯（ylb-lamp）功能，支持多种测试套件：极简测试（4步快速验证核心链路）、冒烟测试（12步完整灯控功能遍历）。用户未指定时默认推荐极简测试并告知耗时。遇到测试台灯/冒烟测试/完整灯控测试/灯控测试/快速台灯测试等时使用。依赖 ylb-lamp-setup 完成的登录状态。
---

# ylb-lamp-test / 光翼灯冒烟测试

## 套件注册表

| 套件 | 触发词 | 脚本 | 耗时 |
|------|--------|------|------|
| 极简测试 | 快速测试 / 验一下 / 随便跑跑 / 4步测试 | scripts/mini_test.py | ~10s |
| 冒烟测试 | 冒烟测试 / 灯控测试 / 全部灯控测试 / 12步测试 | scripts/smoke_test.py | ~60s |

> 用户未明确指定时，默认推荐**极简测试**，告知预计耗时，询问是否继续。

---

## 执行规范

### 1. 前置检查（每次执行前必做）

```bash
SKILL_DIR=~/.openclaw/skills/ylb-lamp-test
TESTS=$SKILL_DIR/scripts
SESSION=~/.openclaw/skills/.ylb-lamp/session.json
DAEMON=~/.openclaw/skills/ylb-lamp-setup/scripts/lamp_daemon.py

# 检查 session
[ -f "$SESSION" ] || {
    echo "❌ session 不存在，请先运行 ylb-lamp-setup 完成登录"
    exit 1
}

# 检查 daemon
pgrep -f lamp_daemon.py > /dev/null || {
    echo "daemon 未运行，正在启动..."
    nohup python3 $DAEMON >> /tmp/lamp_daemon.log 2>&1 &
    for i in $(seq 1 10); do
        sleep 1
        grep -q "MQTT连接 rc=Success" /tmp/lamp_daemon.log 2>/dev/null && break
    done
    echo "daemon 已就绪"
}
```

### 2. 执行套件

```bash
python3 $TESTS/<套件脚本名>
```

### 3. 执行后处理

- 把终端输出**原文**告诉用户
- 询问："每一步台灯都有响应吗？有没有哪步没反应？"
- 用户反馈问题时，按以下顺序排查：
  1. daemon 是否在跑：`pgrep -f lamp_daemon.py`
  2. daemon 日志有无报错：`tail -20 /tmp/lamp_daemon.log`
  3. session 是否有效（token 是否过期）
  4. 队列文件是否可写：`echo test > /tmp/lamp_cmd_queue.txt`

---

## 新增套件说明

新增测试套件只需两步，详见 `scripts/README.md`：
1. 在 `scripts/` 目录新建脚本（使用 README 中的模板）
2. 在本文件的套件注册表中加一行

---

## 常见问题

| 现象 | 排查方向 |
|------|----------|
| 脚本跑完但灯没动 | daemon 未运行，或队列文件权限问题 |
| TTS 没声音但灯有响应 | 音量是否被调到 0，或 TTS 内容超 150 字 |
| 中途卡住不动 | `time.sleep` 等待期间正常，等完即继续 |
| 报 FileNotFoundError | `/tmp/lamp_cmd_queue.txt` 路径权限问题，检查 /tmp 可写性 |
