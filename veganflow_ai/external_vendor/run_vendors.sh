#!/bin/bash

# 1. Kill any zombie vendors from previous runs
echo "🧹 Cleaning up old vendor processes..."
pkill -f "vendor_agent.py"

echo "🌱 Spawning the VeganFlow Vendor Ecosystem..."
echo "---------------------------------------------------"

# 2. Launch Vendors (Background Processes)
# Format: python veganflow_ai/external_vendor/vendor_agent.py --name "Name" --port PORT --reliability SCORE &

# --- Broadline Distributors ---
python veganflow_ai/external_vendor/vendor_agent.py --name "Earthly Gourmet" --port 8001 --reliability 0.98 &
python veganflow_ai/external_vendor/vendor_agent.py --name "Feesers Food Dst" --port 8002 --reliability 0.92 &
python veganflow_ai/external_vendor/vendor_agent.py --name "Clark Distributing" --port 8003 --reliability 0.88 &
python veganflow_ai/external_vendor/vendor_agent.py --name "LCG Foods" --port 8004 --reliability 0.95 &

# --- Artisanal Makers ---
python veganflow_ai/external_vendor/vendor_agent.py --name "Miyokos Creamery" --port 8005 --reliability 0.99 &
python veganflow_ai/external_vendor/vendor_agent.py --name "Rebel Cheese" --port 8006 --reliability 0.96 &
python veganflow_ai/external_vendor/vendor_agent.py --name "Treeline Cheese" --port 8007 --reliability 0.94 &

# --- Specialists ---
python veganflow_ai/external_vendor/vendor_agent.py --name "The Vreamery" --port 8008 --reliability 0.97 &
python veganflow_ai/external_vendor/vendor_agent.py --name "The BE Hive" --port 8009 --reliability 0.93 &
python veganflow_ai/external_vendor/vendor_agent.py --name "All Vegetarian Inc" --port 8010 --reliability 0.85 &
python veganflow_ai/external_vendor/vendor_agent.py --name "FakeMeats.com" --port 8011 --reliability 0.99 &

# 3. Wait for startup
sleep 3
echo "---------------------------------------------------"
echo "✅ 11 Vendor Agents are active and listening via A2A."
echo "   - Earthly Gourmet is on Port 8001"
echo "   - FakeMeats.com is on Port 8011"
echo ""
echo "To stop them later, run: pkill -f vendor_agent.py"