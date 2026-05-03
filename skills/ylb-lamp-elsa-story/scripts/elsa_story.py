#!/usr/bin/env python3
"""
艾莎公主1分钟双语故事 - 灯光+语音同步脚本
专为元萝卜光翼灯设计，逐句时间轴控制
"""

import time, json

CMD_FILE = "/tmp/lamp_cmd_queue.txt"

def mq(cmd_data):
    with open(CMD_FILE, "w") as f:
        f.write(json.dumps(cmd_data))

def tts(text):
    with open(CMD_FILE, "w") as f:
        f.write(json.dumps({
            "event": "claw-skill",
            "value": {
                "skill": "skill-tts-chinese",
                "content": text
            }
        }))

def set_light(mode, brightness, temperature):
    mq({
        "event": "adjust_brightness",
        "value": {
            "brightness_mode": mode,
            "brightness": brightness,
            "temperature": temperature
        }
    })

# ========== 灯光配置表 ==========
# (brightness_mode, brightness, temperature)
# brightness_mode: 0=泛光, 1=聚光 | temperature: 1=最冷, 4=最暖
SCENES = [
    (0, 3, 1),   # 0:00-0:08 泛光+冷色+中等亮度
    (1, 4, 1),   # 0:08-0:18 聚光+冷色+稍亮
    (0, 2, 1),   # 0:18-0:28 泛光+冷色+稍暗
    (0, 3, 4),   # 0:28-0:40 泛光+暖色+中等亮度
    (1, 3, 4),   # 0:40-0:52 聚光+暖色+柔和亮
    (0, 1, 4),   # 0:52-1:00 泛光+暖色+慢慢变暗
]

# ========== 故事文本 ==========
LINES = [
    ("在遥远的北方，有一座冰雪城堡。", "In the far north, there is an ice castle."),
    ("艾莎公主有冰雪魔法。", "Princess Elsa has ice magic."),
    ("雪花在空中轻轻飞舞。", "Snowflakes fly in the sky."),
    ("最强大的魔法，是善良与勇敢。", "The strongest magic is kindness and bravery."),
    ("相信自己，你就是最棒的小公主。", "Believe in yourself. You are a great princess."),
    ("艾莎的故事讲完啦，下次再见。", "See you next time."),
]

def run():
    print("=" * 40)
    print("艾莎公主1分钟双语故事 开始")
    print("=" * 40)

    mq({"event": "switch_device_onoff", "value": 1})
    time.sleep(1)

    start = time.time()

    for i, ((mode, brightness, temp), (cn, en)) in enumerate(zip(SCENES, LINES)):
        elapsed = time.time() - start
        print(f"\n[{elapsed:.1f}s] 第{i+1}段")
        print(f"  中文: {cn}")
        print(f"  英文: {en}")

        set_light(mode, brightness, temp)
        time.sleep(0.5)

        tts(cn)
        time.sleep(len(cn) * 0.4 + 1.0)

        tts(en)
        time.sleep(len(en.split()) * 0.5 + 1.0)

        print(f"  完成")

    set_light(0, 1, 4)
    print("\n" + "=" * 40)
    print("艾莎公主1分钟双语故事 结束")
    print("=" * 40)

if __name__ == "__main__":
    run()
