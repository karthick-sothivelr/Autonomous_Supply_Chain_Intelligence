import uvicorn
import os
from fastapi import FastAPI
from dotenv import load_dotenv

# Import your existing creator function
from veganflow_ai.external_vendor.vendor_agent import create_vendor_agent

# Load env for API keys
load_dotenv()

# 1. The Main Container App
app = FastAPI(title="VeganFlow Vendor Ecosystem")

# 2. Define our Vendors (Same list as your DB)
vendors_config = [
    {"slug": "earthly", "name": "Earthly Gourmet", "reliability": 0.98},
    {"slug": "feesers", "name": "Feesers Food Dst", "reliability": 0.92},
    {"slug": "clark",   "name": "Clark Distributing", "reliability": 0.88},
    {"slug": "lcg",     "name": "LCG Foods", "reliability": 0.95},
    {"slug": "miyokos", "name": "Miyokos Creamery", "reliability": 0.99},
    {"slug": "rebel",   "name": "Rebel Cheese", "reliability": 0.96},
    {"slug": "treeline","name": "Treeline Cheese", "reliability": 0.94},
    {"slug": "vreamery","name": "The Vreamery", "reliability": 0.97},
    {"slug": "behive",  "name": "The BE Hive", "reliability": 0.93},
    {"slug": "allveg",  "name": "All Vegetarian Inc", "reliability": 0.85},
    {"slug": "fakemeats","name": "FakeMeats.com", "reliability": 0.99},
]

# 3. Mount each agent as a sub-application
print("🚀 Initializing Vendor Hub...")
for v in vendors_config:
    # Note: We pass port=8080 but it doesn't matter for sub-apps
    # The crucial part is the mount path
    agent_app = create_vendor_agent(v['name'], v['reliability'], port=8080)
    
    # Mount at /slug (e.g., /earthly)
    app.mount(f"/{v['slug']}", agent_app)
    print(f"   ✅ Mounted: {v['name']} -> /{v['slug']}")

@app.get("/")
def health_check():
    return {"status": "Vendor Hub Online", "vendors": len(vendors_config)}

if __name__ == "__main__":
    # Cloud Run expects listening on 0.0.0.0 and the PORT env var
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
