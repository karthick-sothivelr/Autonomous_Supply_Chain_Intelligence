import os
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types

# Import our specialized sub-agents (use package-relative imports)
from .inventory import create_shelf_monitor
from .procurement import create_procurement_agent

# --- Automation: The Memory Hook ---
async def auto_save_memory(callback_context):
    """
    AUTOMATION HOOK: Runs automatically after every agent turn.
    It pushes the session history to the Memory Service for consolidation.
    """
    # Check if memory service is available in the runner context
    if not hasattr(callback_context._invocation_context, 'memory_service'):
        return

    memory_service = callback_context._invocation_context.memory_service
    session = callback_context._invocation_context.session
    
    if memory_service:
        print(f"   🧠 [Auto-Memory] Ingesting session insights...")
        await memory_service.add_session_to_memory(session)

def create_store_manager():
    """
    Creates the 'VeganFlow' Store Manager (Root Agent).
    """
    # Use Gemini 2.5 Pro for high-level reasoning and delegation
    model_config = Gemini(
        model="gemini-2.5-pro",
        retry_options=types.HttpRetryOptions(attempts=3)
    )

    # Initialize the Workers
    inventory_agent = create_shelf_monitor()
    procurement_agent = create_procurement_agent()

    system_instruction = """
    You are the Store Manager for 'VeganFlow', a high-tech sustainable retail store.
    Your goal is to optimize inventory costs, prevent waste, and ensure affordability.
    
    You manage a team of specialized agents. DO NOT attempt to solve tasks yourself.
    DELEGATE immediately based on the user's request:
    
    --- YOUR TEAM ---
    1. shelf_monitor (Inventory Agent):
       - The "Eyes" of the store.
       - Use this for ANY questions about stock levels, sales velocity, or expiry dates.
       - Example: "Do we have enough Oat Milk?" or "What is expiring soon?"
       
    2. procurement_negotiator (Procurement Agent):
       - The "Hands" of the store.
       - Use this ONLY when you need to buy stock, contact vendors, or check market prices.
       - Example: "Restock the Cashew Cheese" or "Negotiate a better price."
    
    --- YOUR PROCESS ---
    1. Analyze the user's request.
    2. If the user asks to "Analyze Risks", call 'shelf_monitor' first.
    3. If the 'shelf_monitor' finds a problem (e.g., Low Stock), AUTOMATICALLY delegate 
       to 'procurement_negotiator' to solve it.
    4. Summarize the final result (Cost Saved / Deal Status) for the store owner clearly.
    """

    store_manager = LlmAgent(
        name="store_manager",
        model=model_config,
        instruction=system_instruction,
        # This creates the hierarchy: Manager -> [Monitor, Negotiator]
        sub_agents=[inventory_agent, procurement_agent],
        # This enables the "Learning" capability
        after_agent_callback=auto_save_memory
    )

    return store_manager

if __name__ == "__main__":
    # Smoke test
    agent = create_store_manager()
    print(f"✅ Root Agent '{agent.name}' initialized.")
    # FIX: Use public 'sub_agents' attribute. 
    # Note: ADK wraps sub-agents in tools, so we iterate carefully.
    if agent.sub_agents:
        print(f"   Sub-agents linked: {len(agent.sub_agents)}")
    else:
        print("   No sub-agents found.")
