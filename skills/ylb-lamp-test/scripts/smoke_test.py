#!/usr/bin/env python3
"""
[套件] 冒烟测试
[步骤] 12步
[耗时] ~60秒
[描述] 完整遍历所有功能：开关灯、音量、聚光/泛光、亮度、色温
[触发] 冒烟测试 / 完整灯控测试 / 灯控测试 / 12步测试
"""

import time, sys, json

QUEUE = "/tmp/lamp_cmd_queue.txt"

# temperature: 1=最冷, 4=最暖  |  brightness_mode: 0=泛光, 1=聚光

def send(cmd, wait=1):
    with open(QUEUE, "w") as f:
        f.write(cmd)
    print(f"  [CMD] {cmd[:60]}{'...' if len(cmd) > 60 else ''}")
    time.sleep(wait)

def tts(text, wait=2):
    send(f"tts:{text}", wait)

def adj(mode, brightness, temperature, wait=1):
    send(json.dumps({
        "event": "adjust_brightness",
        "value": {"brightness_mode": mode, "brightness": brightness, "temperature": temperature}
    }), wait)

def step(n, desc):
    print(f"\n[{n}/12] {desc}")

def main():
    print("开始灯控测试")
    tts("开始灯控测试")
    
    # Step 1: 开灯
    step(1, "开灯")
    tts("开灯")
    send("switch_device_onoff:1")
    
    # Step 2: 音量→最大
    step(2, "音量→最大")
    # tts("音量调到最大")
    send('{"event":"adjust_volume","value":10}')
    tts("音量已调到最大")

    # Step 3: 音量→最小
    step(3, "音量→最小")
    # tts("音量调到最小")
    send('{"event":"adjust_volume","value":1}')
    tts("音量已调到最小")

    # Step 4: 聚光模式
    step(4, "聚光模式（专注阅读）")
    tts("聚光灯")
    adj(1, 3, 3)
    tts("专注阅读模式")

    # Step 5: 亮度→最大（聚光模式下）
    step(5, "亮度→最大")
    tts("亮度调到最大")
    adj(1, 5, 3)
    # tts("亮度已调到最大")

    # Step 6: 亮度→最小（聚光模式下）
    step(6, "亮度→最小")
    tts("亮度调到最小")
    adj(1, 1, 3)
    # tts("亮度已调到最小")

    # Step 7: 标准照明（泛光）
    step(7, "标准照明模式")
    tts("泛光灯")
    adj(0, 3, 3)
    tts("标准照明模式")

    # Step 8: 亮度→最大（泛光模式下）
    step(8, "亮度→最大")
    tts("亮度调到最大")
    adj(0, 5, 3)
    # tts("亮度已调到最大")

    # Step 9: 亮度→最小（泛光模式下）
    step(9, "亮度→最小")
    tts("亮度调到最小")
    adj(0, 1, 3)
    # tts("亮度已调到最小")

    # Step 10: 色温→最冷（temperature=1）
    step(10, "色温→最冷")
    tts("色温调到最冷")
    adj(0, 3, 1)
    #tts("色温已调到最冷")

    # Step 11: 色温→最暖（temperature=4）
    step(11, "色温→最暖")
    tts("色温调到最暖")
    adj(0, 3, 4)
    #tts("色温已调到最暖")

    # Step 12: 关灯
    step(12, "关灯")
    tts("关灯")
    send("switch_device_onoff:0")
    
    tts("测试完成")

    print("\n" + "=" * 44)
    print("全部 12 项测试已发送，请观察台灯实际变化确认")
    print("=" * 44)

if __name__ == "__main__":
    main()
