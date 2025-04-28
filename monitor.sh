#!/bin/bash

# Monitoring script for Berlin Transport History Project
# Run this periodically to check system health

echo "===================================================="
echo "Berlin Transport History Monitoring - $(date)"
echo "===================================================="

# Check if containers are running
echo "Checking container status..."
container_status=$(docker-compose ps --format json | jq -r '.[].State')
if [[ $container_status == *"running"* && ! $container_status == *"exited"* && ! $container_status == *"dead"* ]]; then
  echo "✅ All containers are running"
else
  echo "❌ One or more containers are not running"
  docker-compose ps
fi

# Check disk space
echo -e "\nChecking disk space..."
disk_usage=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$disk_usage" -gt 90 ]; then
  echo "❌ CRITICAL: Disk usage is at ${disk_usage}%"
elif [ "$disk_usage" -gt 80 ]; then
  echo "⚠️ WARNING: Disk usage is at ${disk_usage}%"
else
  echo "✅ Disk usage is at ${disk_usage}%"
fi

# Check memory usage
echo -e "\nChecking memory usage..."
memory_usage=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
if [ "$memory_usage" -gt 90 ]; then
  echo "❌ CRITICAL: Memory usage is at ${memory_usage}%"
elif [ "$memory_usage" -gt 80 ]; then
  echo "⚠️ WARNING: Memory usage is at ${memory_usage}%"
else
  echo "✅ Memory usage is at ${memory_usage}%"
fi

# Check if the site is accessible
echo -e "\nChecking website accessibility..."
site_status=$(curl -s -o /dev/null -w "%{http_code}" https://berlin-transport-history.de)
if [ "$site_status" -eq 200 ] || [ "$site_status" -eq 301 ] || [ "$site_status" -eq 302 ]; then
  echo "✅ Website is accessible (HTTP ${site_status})"
else
  echo "❌ Website is NOT accessible (HTTP ${site_status})"
fi

# Check for errors in logs
echo -e "\nChecking for errors in logs..."
backend_errors=$(grep -i "error" logs/backend/*.log 2>/dev/null | wc -l)
if [ "$backend_errors" -gt 0 ]; then
  echo "⚠️ Found ${backend_errors} errors in backend logs"
  echo "Recent errors:"
  grep -i "error" logs/backend/*.log 2>/dev/null | tail -5
else
  echo "✅ No errors found in backend logs"
fi

# Check Cloudflare Tunnel status if cloudflared is installed
if command -v cloudflared &> /dev/null; then
  echo -e "\nChecking Cloudflare Tunnel status..."
  tunnel_status=$(cloudflared tunnel info | grep -i "status")
  if [[ $tunnel_status == *"active"* ]]; then
    echo "✅ Cloudflare Tunnel is active"
  else
    echo "❌ Cloudflare Tunnel is not active"
    echo "$tunnel_status"
  fi
fi

echo -e "\n===================================================="
echo "Monitoring completed"
echo "Run this script periodically to ensure system health"
echo "===================================================="

# To run this automatically, add to crontab:
# */15 * * * * /path/to/berlin-transport-project/monitor.sh >> /path/to/berlin-transport-project/logs/monitoring.log 2>&1
