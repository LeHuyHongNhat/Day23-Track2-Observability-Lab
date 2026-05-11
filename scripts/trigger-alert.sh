#!/usr/bin/env bash
## Trigger an alert by killing the app, wait for FIRE + RESOLVE.
set -euo pipefail

echo "Step 1: kill app container"
docker stop day23-app >/dev/null

echo "Step 2: wait up to 120s for ServiceDown to reach FIRING state"
FIRED=0
for i in $(seq 1 30); do
  sleep 4
  state=$(curl -fsS http://127.0.0.1:9090/api/v1/alerts 2>/dev/null | python3 -c "
import json,sys
for a in json.load(sys.stdin)['data']['alerts']:
    if a['labels'].get('alertname') == 'ServiceDown':
        print(a['state'])
        break
" 2>/dev/null || echo "none")
  echo "  tick $((i*4))s: ServiceDown=${state}"
  if [ "$state" = "firing" ]; then
    echo ""
    echo ">>> 🔥 ALERT IS FIRING — screenshot Alertmanager + Slack NOW <<<"
    echo ">>> http://127.0.0.1:9093/#/alerts <<<"
    FIRED=1
    break
  fi
done

if [ "$FIRED" -eq 0 ]; then
  echo "WARNING: ServiceDown did not fire — check Prometheus rules"
fi

# Wait for Alertmanager to process + send to Slack
echo ""
echo "Waiting 45s for Alertmanager to process and send to Slack..."
sleep 45

echo "Step 3: restart app"
docker start day23-app >/dev/null

echo "Step 4: wait up to 120s for alert to resolve"
for i in $(seq 1 30); do
  sleep 4
  # Check if ServiceDown is gone from Prometheus
  state=$(curl -fsS http://127.0.0.1:9090/api/v1/alerts 2>/dev/null | python3 -c "
import json,sys
found=False
for a in json.load(sys.stdin)['data']['alerts']:
    if a['labels'].get('alertname') == 'ServiceDown':
        print(a['state'])
        found=True
        break
if not found:
    print('gone')
" 2>/dev/null)
  echo "  tick $((i*4))s: ServiceDown=${state}"
  if [ "$state" = "gone" ] || [ -z "$state" ]; then
    echo ""
    echo ">>> ✅ ALERT RESOLVED — screenshot Slack for resolved message <<<"
    exit 0
  fi
done

echo "Alert did not resolve within 120s" >&2
exit 1
