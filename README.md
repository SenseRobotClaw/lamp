### 
这是元萝卜（YuanLuoBo）光翼灯/龙虾灯/SenseRobot Lamp的 OpenClaw Skills 框架

包含最基本的安装 Skill (ylb-lamp-setup) 和测试 Skill（ylb-lamp-test），以及可以扩展到多个应用场景的使用 Skill (ylb-lamp-*)。
例如：
1. 讲故事 （ylb-lamp-elsa-story）
2. 正念练习（ylb-lamp-mindbreath）

统一使用 ylb-lam- 前缀，便于用户在各自终端上的查询

这些 Skill 的安装次序必须是先安装 setup skill，接着再安装 test skill 以及其他的应用 skills。
如果卸载光翼灯skill / 或退出登录，它会把 setup 及 session 还有用户的设备信息都删掉，那么其他的那些测试和应用的 Skill 就都不能工作了。

## 部署到OpenClaw之后的目标目录结构

```
~/.openclaw/skills/
│
├── .ylb-lamp/                        ← 三个 Skill 共用的运行时数据（不进 git）
│   ├── session.json                  ← 登录凭证（运行时生成）
│   ├── device_info.json              ← 设备信息（运行时生成）
│
├── ylb-lamp-setup/                   ← Skill 1：登录 & 初始化
│   ├── SKILL.md
│   └── scripts/                      ← 公共原子脚本（进 git）
│       ├── lamp_daemon.py
│       ├── lamp_photo.py
│       └── lamp_cloudcontrol/
│           ├── server.js
│           ├── .env                  ← 不进 git
│           └── .env.example          ← 进 git
│   └── references/
│       ├── auth-api.md
│       ├── operations.md
│       ├── environment.md
│       ├── reporting.md
│       ├── api-matrix.md
│       └── trigger-map.md
│
├── ylb-lamp-test/                    ← Skill 2：功能测试
│   ├── SKILL.md
│   └── test_cases/                   ← 可选，测试用例
│
└── ylb-lamp-mindbreath/                    ← Skill 3：场景演示
    ├── SKILL.md
    └── scenes/                       ← 可选，演示场景配置

# 命令队列
/tmp/lamp_cmd_queue.txt      ← 即时、共享、重启自动清理

# daemon 日志
/tmp/lamp_daemon.log         ← 临时日志，放 /tmp/

# lamp_photo 数据 拍照临时存储（运行时生成）
/tmp/lamp_photos/photo_YYYYMMDD_HHMMSS.jpg   ← 临时存储从台灯抓取的照片
