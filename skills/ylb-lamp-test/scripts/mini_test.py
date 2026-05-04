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

def send(cmd, wait=1):
    with open(QUEUE, "w") as f:
        f.write(cmd)
    print(f"  [CMD] {cmd[:60]}{'...' if len(cmd) > 60 else ''}")
    time.sleep(wait)

def tts(text, wait=2):
    send(f"tts:{text}", wait)

def adj(mode, brightness, temperature, wait=1):
    send(json.dumps({"event":"adjust_brightness","value":{"brightness_mode":mode,"brightness":brightness,"temperature":temperature}}), wait)

def main():
    print("极简测试 开始")
    tts("开灯");  send("switch_device_onoff:1", wait=2)
    tts("聚光灯"); adj(1, 3, 3, wait=4)
    tts("泛光灯"); adj(0, 3, 3, wait=2)
    tts("关灯");  send("switch_device_onoff:0")
    tts("测试完成")
    print("测试完成")

if __name__ == "__main__":
    main()