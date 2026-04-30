# HEARTBEAT.md

## 桥接进程（lamp_daemon）健康检查

每 8 次心跳检查一次（约每 4 小时，心跳间隔约 30 分钟）。自动拉起，不通知用户。

```bash
# 路径自动检测，不需要用户配置
WORKDIR=""
for d in "${LIGHTWING_WORKDIR:-}" "$HOME/.openclaw/workspace" "$HOME/.openclaw"; do
    [ -d "$d" ] && WORKDIR="$d" && break
done
DAEMON="${WORKDIR}/scripts/lamp_daemon.py"
OPENCLAW="${LIGHTWING_OPENCLAW:-${HOME}/.npm-global/bin/openclaw}"

COUNTER_FILE="/tmp/lamp_health_counter"
COUNT=$(cat "$COUNTER_FILE" 2>/dev/null || echo 0)
NEXT=$(( (COUNT + 1) % 8 ))
echo "$NEXT" > "$COUNTER_FILE"
[ "$NEXT" -ne 0 ] && exit 0

if ! pgrep -f lamp_daemon.py > /dev/null; then
    nohup python3 "$DAEMON" >> /tmp/lamp_daemon.log 2>&1 &
fi

# 跨平台：用 sed 提取时间戳，用 python3 做时间比较（兼容 macOS / Linux）
LAST_MQTT=$(grep "MQTT连接" /tmp/lamp_daemon.log 2>/dev/null | tail -1 | sed 's/\[\([0-9:]*\)\].*/\1/')
if [ -n "$LAST_MQTT" ]; then
    STALE=$(python3 -c "
import time
ts='$LAST_MQTT'
try:
    h,m,s=map(int,ts.split(':'))
    t=time.localtime()
    then=time.mktime((t.tm_year,t.tm_mon,t.tm_mday,h,m,s,0,0,-1))
    diff=time.time()-then
    if diff<0: diff+=86400
    print('1' if diff>180 else '0')
except: print('0')
" 2>/dev/null)
    if [ "$STALE" = "1" ]; then
        pkill -f lamp_daemon.py
        sleep 1
        nohup python3 "$DAEMON" >> /tmp/lamp_daemon.log 2>&1 &
    fi
fi
```

## 灯通知检查

每次心跳检查通知队列：

```bash
QUEUE=""
for d in "${LIGHTWING_QUEUE:-}" "$HOME/.openclaw/workspace/.lightwing/notify_queue.txt" \
           "$HOME/.openclaw/.lightwing/notify_queue.txt"; do
    [ -s "$d" ] && QUEUE="$d" && break
done
[ -z "$QUEUE" ] && exit 0

MSG=$(tail -1 "$QUEUE" | sed 's/\[[0-9:]*\] //')
[ -z "$MSG" ] && exit 0

OPENCLAW="${LIGHTWING_OPENCLAW:-${HOME}/.npm-global/bin/openclaw}"
TARGET="${LIGHTWING_FEISHU_TARGET:-}"

if [ -n "$TARGET" ]; then
    "$OPENCLAW" message send --channel feishu --target "$TARGET" --message "$MSG" > /dev/null 2>&1
else
    # 自动找 feishu direct session
    export MSG OPENCLAW
    python3 - <<'PYEOF'
import subprocess, os
msg = os.environ["MSG"]
openclaw = os.environ["OPENCLAW"]
r = subprocess.run([openclaw, "sessions", "list"], capture_output=True, text=True, timeout=10)
for line in r.stdout.strip().split("\n"):
    if "feishu" in line.lower() and "direct" in line.lower():
        for p in line.split():
            if p.startswith("agent:"):
                sk = p.rstrip(",")
                subprocess.run([openclaw, "sessions", "send", sk, msg],
                             capture_output=True, timeout=15)
                break
        break
PYEOF
fi
> "$QUEUE"
```

通知进程（`lamp_daemon.py`）已对状态变化去重，仅在有意义的变化时写入队列。发送完成后清空文件。

## lamp_cloudcontrol 服务健康检查（拍照判题依赖）

每 8 次心跳检查一次（约每 4 小时）。

```bash
COUNTER_FILE="/tmp/lamp_cloudcontrol_health_counter"
COUNT=$(cat "$COUNTER_FILE" 2>/dev/null || echo 0)
NEXT=$(( (COUNT + 1) % 8 ))
echo "$NEXT" > "$COUNTER_FILE"
[ "$NEXT" -ne 0 ] && exit 0

# lamp_cloudcontrol 服务检查（拍照判题依赖）
CLOUD_CTRL_DIR="$HOME/.openclaw/workspace/imported/openclaw4lamp-main/lamp_cloudcontrol"
if ! pgrep -f "node.*server.js" > /dev/null 2>&1; then
    cd "$CLOUD_CTRL_DIR"
    nohup node server.js >> /tmp/lamp_cloudcontrol.log 2>&1 &
fi
# 验证服务就绪（最多等5秒）
for i in $(seq 1 5); do
    sleep 1
    if curl -s --max-time 2 http://localhost:3001/health | grep -q "ok"; then
        break
    fi
done
```
