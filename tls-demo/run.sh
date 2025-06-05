# renew.sh  – naive loop; use cron/systemd-timer if you prefer
while true; do
  python cert_forge.py server
  python cert_forge.py client
  pkill -HUP -f "python server.py"   # ask uvicorn process to reload context
  sleep 240                          # 4 min
done
