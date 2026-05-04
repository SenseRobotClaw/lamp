# 说明
这是元萝卜（YuanLuoBo）光翼灯/龙虾灯/SenseRobot Lamp的 OpenClaw Skills 框架

## 官方技能地址
元萝卜龙虾灯功能安装：
https://github.com/SenseRobotClaw/lamp/tree/main/skills/ylb-lamp-setup
元萝卜龙虾灯冒烟测试 ：
https://github.com/SenseRobotClaw/lamp/tree/main/skills/ylb-lamp-test
元萝卜龙虾灯2分钟正念练习：
https://github.com/SenseRobotClaw/lamp/tree/main/skills/ylb-lamp-mind-breath
元萝卜龙虾灯爱莎公主双语故事：
https://github.com/SenseRobotClaw/lamp/tree/main/skills/ylb-lamp-elsa-story

## 元萝卜龙虾灯命名规则
* 基本功能安装 Skill (ylb-lamp-setup) 
* 灯控冒烟测试 Skill（ylb-lamp-test）
* 扩展到不同应用场景的应用 Skills (ylb-lamp-*)。
例如：
1. 讲故事 （ylb-lamp-elsa-story）
2. 正念练习（ylb-lamp-mindbreath）

统一使用 ylb-lam- 前缀，便于用户在各自终端上的查询

## 安装次序
这些 Skill 的安装次序必须是先安装 setup skill，接着再安装 test skill 以及其他的应用 skills。
如果卸载光翼灯skill / 或退出登录，它会把 setup 及 session 还有用户的设备信息都删掉，那么其他的那些测试和应用的 Skill 就都不能工作了。

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

## API 

### MQTT 

开关灯 MQTT 接口
```                                                                                                   
  Payload 格式    
                                                                                                 
  开灯：          
  {
    "timestamp": 1746461234,
    "seq": "a3f7c2d18b094e51a068bc34e34ac5a7",
    "signal": 7,                                                                                 
    "data": {                                                                                    
      "event": "switch_device_onoff",                                                            
      "value": 1                                                                                 
    }             
  }                                                                                              
                  
  关灯：
  {
    "timestamp": 1746461234,
    "seq": "a3f7c2d18b094e51a068bc34e34ac5a7",
    "signal": 7,                                                                                 
    "data": {   
      "event": "switch_device_onoff",                                                            
      "value": 0  
    }                                                                                            
  }
                                                                                                 
  队列文件写法    

  # 开灯
  echo 'switch_device_onoff:1' > /tmp/lamp_cmd_queue.txt                                         
   
  # 关灯                                                                                         
  echo 'switch_device_onoff:0' > /tmp/lamp_cmd_queue.txt
```                                                                     

亮度 / 色温 / 显示模式 MQTT 接口                     
 ```                                                                                                
  Payload 格式                                                                                   
                                                                                                 
  {                                                                                              
    "timestamp": 1746461234,                                                                     
    "seq": "a3f7c2d18b094e51a068bc34e34ac5a7",                                                   
    "signal": 7,                                                                                 
    "data": {                                                                                    
      "event": "adjust_brightness",                                                              
      "value": {  
        "brightness_mode": 0,
        "brightness": 3,                                                                         
        "temperature": 2
      }                                                                                          
    }             
  }

  字段取值

  ┌─────────────────┬───────┬──────────────────────────────────────┐                             
  │      字段       │ 取值  │                 说明                 │
  ├─────────────────┼───────┼──────────────────────────────────────┤                             
  │ brightness_mode │ 0 / 1 │ 0 = 泛光，1 = 聚光                   │
  ├─────────────────┼───────┼──────────────────────────────────────┤
  │ brightness      │ 1–5   │ 亮度，1 最暗，5 最亮                 │                             
  ├─────────────────┼───────┼──────────────────────────────────────┤                             
  │ temperature     │ 1–4   │ 色温，1 最冷，4 最暖；仅泛光模式有效 │                             
  └─────────────────┴───────┴──────────────────────────────────────┘                             
                  
  队列文件写法                                                                                   
                  
  echo                                                                                           
  '{"event":"adjust_brightness","value":{"brightness_mode":0,"brightness":3,"temperature":2}}' > 
  /tmp/lamp_cmd_queue.txt                                                     
```

TTS 语音播报接口
```                                                                                             
  队列文件 /tmp/lamp_cmd_queue.txt 内容                                                          
                                                                                                 
  写法一（推荐简写）：                                                                           
  tts:test阅读指令                                                                               
                  
  写法二（JSON 格式）：                                                                          
  {"event": "claw-skill", "value": {"skill": "skill-tts-chinese", "content": "test阅读指令"}}
                                                                                                 
  两种写法 daemon 都能识别，最终发出的 MQTT payload 完全相同。                                   
                                                                                                 
  ---                                                                                            
  最终发到 MQTT Broker 的 Payload                                                                
                                                                                                 
  {
    "timestamp": 1746461234,                                                                     
    "seq": "a3f7c2d18b094e51a068bc34e34ac5a7",
    "signal": 7,                                                                                 
    "data": {
      "event": "claw-skill",                                                                     
      "value": {                                                                                 
        "skill": "skill-tts-chinese",
        "content": "test阅读指令"                                                                
      }           
    }
  }

     
```

MQTT skill-take-photo 接口格式
```
  {                                                                                              
    "timestamp": 1746461234,                                                                     
    "seq": "a3f7c2d18b094e51a068bc34e34ac5a7",                                                   
    "signal": 7,                                                                                 
    "data": {                                                                                    
      "event": "claw-skill",                                                                     
      "value": {                                                                                 
        "skill": "skill-take-photo"
      }                                                                                          
    }             
  }

    设备回包（监听 status topic）
  {
    "data": {                                                                                    
      "skill-take-photo": {
        "result": "success",                                                                     
        "objectname": "<云端图片路径>"
      }                                                                                          
    }
  }                                                                                              
        
```
