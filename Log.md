# 说明
这是元萝卜（YuanLuoBo）光翼灯/龙虾灯/SenseRobot Lamp for OpenClaw Skills 框架


## 部署到OpenClaw之后的目标目录结构

```
~/.openclaw/skills/
│
├── .ylb-lamp/                        ← 三个 Skill 共用的运行时数据（不进 git）
│   ├── session.json                  ← 登录凭证（运行时生成）
│   └── device_info.json              ← 设备信息（运行时生成）
│
├── ylb-lamp-setup/                   ← Skill 1：登录 & 初始化
│   ├── SKILL.md
│   ├── scripts/                      ← 公共原子脚本（进 git）
│   │   ├── lamp_daemon.py
│   │   ├── lamp_photo.py
│   ├── references/
│   │   ├── auth-api.md
│   │   ├── operations.md
│   │   ├── environment.md
│   │   ├── reporting.md
│   │   ├── api-matrix.md
│   │   └── trigger-map.md
│	│
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
```

## 工作日志
### 2026-05-03： ylb-lamp 系列技能开发与重构                                                                  

1. Skills 命名规范调整（ce193ea）                                                          
                                                                                             
  - 将所有 skill 统一改为 ylb-lamp- 前缀命名规范                                             
  - 重新整理了 skills/ 目录结构                                                              
                                                                                             
  2. 新增 4 个 Skills（2443324）                                                             
                                                                                             
  ┌──────────────────────┬────────────────────────────────────────────────────────────────┐  
  │        Skill         │                              说明                              │
  ├──────────────────────┼────────────────────────────────────────────────────────────────┤  
  │ ylb-lamp-setup       │ 登录 & 初始化，核心基础 Skill，含认证、设备信息、daemon 脚本等 │
  ├──────────────────────┼────────────────────────────────────────────────────────────────┤  
  │ ylb-lamp-test        │ 灯控冒烟测试 Skill                                             │  
  ├──────────────────────┼────────────────────────────────────────────────────────────────┤  
  │ ylb-lamp-mind-breath │ 2 分钟正念练习场景                                             │  
  ├──────────────────────┼────────────────────────────────────────────────────────────────┤  
  │ ylb-lamp-elsa-story  │ 爱莎公主双语故事场景                                           │
  └──────────────────────┴────────────────────────────────────────────────────────────────┘  
                  
  主要新增脚本：                                                                             
  - lamp_daemon.py — 后台守护进程
  - lamp_photo.py — 拍照功能                                                                 
  - mind_breath.py — 正念练习逻辑
  - elsa_story.py — 故事播放逻辑                                                             
  - 多份 references/ 文档（API、认证、操作、触发器等）
                                                                                             
  3. 更新 README（dae0534）                                                                  
                                                                                             
  - 补充了 4 个 skill 的官方 GitHub 链接                                                     
  - 说明了命名规范（ylb-lamp- 前缀）                                                         
  - 明确了安装顺序：先 setup → 再 test → 再应用 skills                                       
  - 描述了部署到 OpenClaw 后的目标目录结构                   

新功能
  - 新增 ylb-lamp-mind-breath 技能：支持呼吸引导 + 灯光控制联动
  - 新增 1 个测试技能和 2 个应用技能                                                                           
  - 完善手机号切换和注销流程的用户指引                                                                                     
  修复                                                                                                                  
  - TTS 语音提示改为在故事讲述和呼吸引导时自动发送                                                                
  - 修正 SKILL.md 中的触发短语，并改进灯光控制函数                                                               
  - 统一通知队列路径为 /tmp/lamp_notify_queue.txt 
  - 统一照片保存目录为 /tmp/lamp_photos                                                                                 
  - 优化 send、announce、adj 函数的响应等待时间                                                                          
  重构与整理                                                                                                            
  - 将环境变量前缀从 LIGHTWING 统一改为 YLBLAMP
  - 统一脚本路径到 ylb-lamp-setup 目录                                                                                  
  - 重命名技能文件夹，统一目录结构    
  - 删除 lightwing_watchdog.py（项目清理）                                                                       
  - 多处文档更新，提升清晰度和一致性                          