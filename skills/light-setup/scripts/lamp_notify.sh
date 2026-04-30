#!/bin/bash
# 自动检测路径，不需要用户配置
LOCK="/tmp/lamp_notify.lock"
if [ -f "$LOCK" ]; then exit 0; fi
touch "$LOCK"
trap "rm -f $LOCK" EXIT

home="${HOME}"
OPENCLAW="${LIGHTWING_OPENCLAW:-${home}/.npm-global/bin/openclaw}"
QUEUE="${LIGHTWING_QUEUE:-${home}/.openclaw/workspace/.lightwing/notify_queue.txt}"
TARGET="${LIGHTWING_FEISHU_TARGET:-}"

if [ ! -s "$QUEUE" ]; then
    exit 0
fi

MSG=$(tail -1 "$QUEUE" | sed 's/\[[0-9:]*\] //')
if [ -z "$MSG" ]; then
    > "$QUEUE"
    exit 0
fi

if [ -n "$TARGET" ]; then
    "$OPENCLAW" message send \
        --channel feishu \
        --target "$TARGET" \
        --message "$MSG" \
        > /dev/null 2>&1
else
    # 自动找 feishu direct session
    export MSG OPENCLAW
    python3 - <<'PYEOF'
import subprocess, os
msg = os.environ.get("MSG", "")
openclaw = os.environ.get("OPENCLAW", "openclaw")
r = subprocess.run([openclaw, "sessions", "list"],
                   capture_output=True, text=True, timeout=10)
for line in r.stdout.strip().split("\n"):
    if "feishu" in line.lower() and "direct" in line.lower():
        for p in line.split():
            if p.startswith("agent:"):
                sk = p.rstrip(",")
                r2 = subprocess.run([openclaw, "sessions", "send", sk, msg],
                                    capture_output=True, text=True, timeout=15)
                print("sent:", sk, r2.returncode)
                break
        break
PYEOF
fi

> "$QUEUE"
