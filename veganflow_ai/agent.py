import logging
import sys
import os

# --- Add current directory to Python Path ---
# This ensures that 'agents' and 'tools' can be imported as top-level modules
# whether running locally via 'adk web' or deployed in the cloud.
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# --- 1. Import Modules ---
from agents.orchestrator import create_store_manager
from tools.retail_database_setup import setup_retail_database

# --- 2. Cloud Initialization ---
# Re-create the ephemeral database every time the agent starts
print("📦 [Cloud Init] Setting up Retail Database schema...")
setup_retail_database()

# --- 3. Define Root Agent ---
# Agent Engine looks for the variable 'root_agent'
print("🤖 [Cloud Init] Initializing VeganFlow Orchestrator...")
root_agent = create_store_manager()

print("✅ [Cloud Init] System Ready.")
