import os
import asyncio
import logging
import sys
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService 
from google.adk.plugins.logging_plugin import LoggingPlugin
from google.genai import types

# --- IMPORT FIX: Pointing to the new 'veganflow_ai' package structure ---
from veganflow_ai.agents.orchestrator import create_store_manager
from veganflow_ai.tools.retail_database_setup import setup_retail_database
from memory_utils import initialize_memory

# --- Configuration and Setup ---

# Load environment variables from .env file
load_dotenv() 

# Set up basic logging (needed for LoggingPlugin output)
if os.getenv("ENABLE_TRACING", "false").lower() == "true":
    logging.basicConfig(level=logging.DEBUG)
    print("🔍 Observability Enabled: Logging set to DEBUG.")
else:
    logging.basicConfig(level=logging.INFO)

async def main():
    """
    Main application entry point for VeganFlow: Autonomous Supply Chain Intelligence.
    """
    print("\n🌱 Starting VeganFlow: Autonomous Supply Chain Intelligence...")
    
    # 1. Initialize the Data and Memory Services
    print("\n[1/3] 📦 Initializing Data Layer...")
    setup_retail_database() # Creates/Resets 'veganflow_store.db'
    
    # Initialize Memory Service (This also seeds the strategy)
    memory_service = await initialize_memory() 
    session_service = InMemorySessionService()

    # 2. Initialize the Orchestrator Agent
    print("[2/3] 🤖 Waking up the Store Manager (Orchestrator)...")
    orchestrator = create_store_manager()
    
    # Create the initial session for the CLI user
    user_id = os.getenv("USER_ID", "ops_manager_01")
    session_id = "main_cli_session"
    app_name = "veganflow_app"

    await session_service.create_session(user_id=user_id, session_id=session_id, app_name=app_name)
    
    # 3. Configure the Runner (The Execution Engine)
    # The runner connects the agent to all services (Memory, Session, Logging)
    print("[3/3] ✅ Configuring Runner and Observability Hook...")
    runner = Runner(
        agent=orchestrator,
        session_service=session_service,
        memory_service=memory_service, # Passes Memory to the Orchestrator and sub-agents
        app_name=app_name,
        plugins=[LoggingPlugin()] # Enables detailed tracing of the agent's thought process
    )
    
    # --- The Interactive Loop ---
    print("-" * 50)
    print(f"🌍 System Online: {orchestrator.name}")
    print("💡 Try typing: 'Analyze inventory risks and resolve them'")
    print("   (Type 'quit' or 'exit' to stop the application)")
    print("-" * 50)

    while True:
        try:
            user_input = await asyncio.to_thread(input, f"\n👤 {user_id}: ")
        except EOFError:
            break
            
        if user_input.lower() in ["quit", "exit"]:
            print("👋 Shutting down VeganFlow.")
            # Note: Background vendor agents need to be killed manually (pkill -f)
            break
            
        print(f"\n🤖 VeganFlow is thinking...")
        
        # Run the full agentic loop (Delegation, A2A calls, Reasoning)
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(parts=[types.Part(text=user_input)])
        ):
            if event.is_final_response():
                print(f"\n🌱 Store Manager:\n{event.content.parts[0].text}")
                
        # Crucial check to yield control for async I/O
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication stopped by user.")