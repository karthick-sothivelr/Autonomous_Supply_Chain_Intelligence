import os
import asyncio
from google.adk.memory import InMemoryMemoryService 
from google.genai import types
from google.adk.sessions import InMemorySessionService
# --- FIX: ADD MISSING IMPORTS ---
from google.adk.runners import Runner  
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini # <-- FIX: Import Gemini
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID")

class MemoryManager:
    def __init__(self):
        """Initializes the memory service instance."""
        self.service = InMemoryMemoryService()
        print("🧠 Memory Manager initialized (InMemory Service).")

    async def seed_memory(self):
        """
        Injects the synthetic history into the Memory Bank using the Session Ingestion pattern.
        """
        print("🌱 Seeding Strategic Targets into Memory...")
        
        # 1. Setup a minimal Seeder Agent and Runner
        seeder_agent = LlmAgent(
            name="memory_seeder",
            # FIX: Gemini is now correctly defined due to import above
            model=Gemini(model="gemini-2.0-flash-lite"), 
            instruction="You are a passive scribe. Acknowledge the user's input with 'Saved.'"
        )
        session_service = InMemorySessionService()
        seed_user_id = "test_user"
        seed_session_id = "seed_session_01"
        seed_app_name = "memory_seeder_app"

        await session_service.create_session(app_name=seed_app_name, user_id=seed_user_id, session_id=seed_session_id)
        
        seeder_runner = Runner(
            agent=seeder_agent,
            session_service=session_service,
            app_name=seed_app_name
        )

        # 2. Strategy to Inject
        strategy_text = "Strategic Goal: For 'Oat Barista Blend', target price is $3.40. Do not pay over $3.60."
        
        # 3. Run the seeder to create conversation history
        async for _ in seeder_runner.run_async(
            user_id=seed_user_id,
            session_id=seed_session_id,
            new_message=types.Content(parts=[types.Part(text=strategy_text)])
        ):
            pass
            
        # 4. Ingest the Session into Memory
        seed_session = await session_service.get_session(app_name=seed_app_name, user_id=seed_user_id, session_id=seed_session_id)
        await self.service.add_session_to_memory(seed_session)
        
        print("✅ Strategies Ingested. Procurement Agent is now context-aware.")
        return self.service

# Helper function to be called from main.py
async def initialize_memory():
    manager = MemoryManager()
    memory_service = await manager.seed_memory()
    return memory_service

if __name__ == "__main__":
    # Test run to verify setup
    print("Running memory setup test...")
    asyncio.run(initialize_memory())