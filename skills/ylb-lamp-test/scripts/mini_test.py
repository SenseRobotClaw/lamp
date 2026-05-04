#!/usr/bin/env python3
"""
[套件] 极简测试
[步骤] 4步
[耗时] ~10秒
[描述] 快速验证开灯、聚光、泛光、关灯核心链路
[触发] 快速测试 / 随便跑跑 / 验一下 / 4步测试
"""
import time, json
QUEUE = "/tmp/lamp_cmd_queue.txt"

def tts(text):
    with open(QUEUE, "w") as f:
        f.write(f"tts:{text}")

def ctrl(cmd):
    with open(QUEUE, "w") as f:
        f.write(cmd)

def adj(mode, b, t):
    ctrl(json.dumps({"event":"adjust_brightness","value":{"brightness_mode":mode,"brightness":b,"temperature":t}}))

print("极简测试 开始")

tts("开灯"); ctrl("switch_device_onoff:1"); time.sleep(2)
tts("聚光灯"); adj(1,3,3); time.sleep(4)
tts("泛光灯"); adj(0,3,3); time.sleep(2)
tts("关灯"); ctrl("switch_device_onoff:0")

print("测试完成")