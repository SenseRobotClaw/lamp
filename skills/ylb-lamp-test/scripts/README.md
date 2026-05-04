# ylb-lamp-test 测试套件说明

## 现有套件

| 文件 | 套件名 | 步骤数 | 耗时 | 触发词 |
|------|--------|--------|------|--------|
| mini_test.py | 极简测试 | 4步 | ~10s | 快速测试 / 验一下 / 随便跑跑 |
| smoke_test.py | 冒烟测试 | 12步 | ~60s | 冒烟测试 / 完整测试 / 全部测试 |


### 灯控极简测试流程（共4项）
| 步骤 | 操作 | TTS 提示（执行前） | 
|------|------|-------------------|
| 1 | 开灯 | "开灯" | 
| 2 | 聚光模式 | "聚光灯，专注阅读" | 
| 3 | 泛光模式 | "泛光灯，标准照明" | 
| 4 | 关灯 | "关灯" |


### 灯控冒烟测试流程（共12项）

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


## 新增套件规范（每次新增只需两步）

### 第一步：新建脚本文件

文件名格式：`<功能>_test.py`，放在本目录下。

脚本模板：

```python
#!/usr/bin/env python3
"""
[套件] <套件名>
[步骤] N步
[耗时] ~Xs
[描述] <一句话描述>
[触发] <触发词1> / <触发词2> / <触发词3>
"""
import time, json

QUEUE = "/tmp/lamp_cmd_queue.txt"

def send(cmd, wait=1):
    with open(QUEUE, "w") as f:
        f.write(cmd)
    print(f"  [CMD] {cmd[:60]}")
    time.sleep(wait)

def tts(text, wait=3):
    send(f"tts:{text}", wait)

def adj(mode, brightness, temperature, wait=1):
    import json
    send(json.dumps({
        "event": "adjust_brightness",
        "value": {"brightness_mode": mode, "brightness": brightness, "temperature": temperature}
    }), wait)

def main():
    print(f"=== <套件名> 开始 ===")
    # 在这里添加测试步骤
    print(f"=== <套件名> 完成 ===")

if __name__ == "__main__":
    main()
```

### 第二步：在 SKILL.md 套件注册表中加一行

打开 `skills/ylb-lamp-test/SKILL.md`，在"## 套件注册表"的表格里追加：

```
| <套件名> | <触发词> | scripts/<文件名>.py | ~Xs |
```

**就这两步，不需要改其他任何文件。**

## 变量约定（所有脚本统一使用）

```python
QUEUE = "/tmp/lamp_cmd_queue.txt"          # 命令队列（多 Skill 公用，重启自动清理）
SESSION = "~/.openclaw/skills/.ylb-lamp/session.json"  # 登录凭证（setup 生成）
SCRIPTS = "~/.openclaw/skills/ylb-lamp-setup/scripts"       # 公共原子脚本
```


