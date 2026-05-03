# HEARTBEAT.md

## 桥接进程（lamp_daemon）健康检查

每 8 次心跳检查一次（约每 4 小时，心跳间隔约 30 分钟）。自动拉起，不通知用户。

```bash
DAEMON="${HOME}/.openclaw/skills/ylb-lamp-setup/scripts/lamp_daemon.py"
OPENCLAW="${YLBLAMP_OPENCLAW:-${HOME}/.npm-global/bin/openclaw}"

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

