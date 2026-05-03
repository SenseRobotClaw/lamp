#!/usr/bin/env python3
"""
2分钟正念呼吸 - 龙虾灯专用
泛光+暖色+偏暗柔和灯光，120秒呼吸引导+语音
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

def set_light(mode=0, brightness=1, temperature=4):
    mq({
        "event": "adjust_brightness",
        "value": {
            "brightness_mode": mode,
            "brightness": brightness,
            "temperature": temperature
        }
    })

# ========== 时间轴 ==========
# (触发秒数, 语音内容)
SCRIPT = [
    (0,   "欢迎来到龙虾灯2分钟正念呼吸。请找一个舒服的姿势，轻轻闭上眼睛。"),
    (20,  "现在，我们慢慢吸气。用鼻子吸气，心里数4秒：一、二、三、四。"),
    (30,  "慢慢呼气，数4秒：一、二、三、四。"),
    (40,  "继续这样呼吸。吸气，放松身体。呼气，放下所有疲惫。"),
    (60,  "把注意力只放在呼吸上。念头飘走也没关系，轻轻拉回来就好。"),
    (80,  "继续安静呼吸。感受这一刻，只属于你自己的平静。"),
    (100, "最后20秒，保持自然、平稳的呼吸。"),
    (115, "准备慢慢回到现实。轻轻活动手指和肩膀。"),
    (120, "2分钟正念练习完成。愿你平静、轻松、充满力量。"),
]

def run():
    print("=" * 40)
    print("2分钟正念呼吸 开始")
    print("=" * 40)

    print("[0s] 开灯 → 泛光+暖色+柔和偏暗")
    mq({"event": "switch_device_onoff", "value": 1})
    time.sleep(1)
    set_light(0, 1, 4)
    time.sleep(0.5)  # 等 daemon 处理完灯光再开始计时

    start = time.time()
    idx = 0
    total = 120

    while True:
        elapsed = time.time() - start

        if idx < len(SCRIPT) and elapsed >= SCRIPT[idx][0]:
            text = SCRIPT[idx][1]
            print(f"\n[{elapsed:.0f}s] {text}")
            tts(text)
            idx += 1

        if elapsed >= total:
            print("\n" + "=" * 40)
            print("2分钟正念呼吸 结束")
            print("=" * 40)
            break

        time.sleep(0.5)

if __name__ == "__main__":
    run()
