import sqlite3
import asyncio
import os
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.tools import load_memory
from google.adk.planners import PlanReActPlanner 
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# --- 1. Market Intelligence Tool (Internal Data) ---

def get_vendor_options(product_name: str) -> str:
    """
    Queries the internal database to find ALL vendors selling a specific product.
    Returns them SORTED by price (Cheapest First).
    """
    conn = sqlite3.connect('veganflow_store.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT product_id, name FROM products WHERE name LIKE ?", (f"%{product_name}%",))
    prod_res = cursor.fetchone()
    
    if not prod_res:
        conn.close()
        return f"❌ Error: Product '{product_name}' not found in the catalog."
    
    pid, full_name = prod_res
    
    sql = """
    SELECT v.name, o.price_wholesale, o.delivery_days, v.reliability_score, v.contact_endpoint
    FROM vendor_offers o
    JOIN vendors v ON o.vendor_id = v.vendor_id
    WHERE o.product_id = ?
    ORDER BY o.price_wholesale ASC
    """
    cursor.execute(sql, (pid,))
    offers = cursor.fetchall()
    conn.close()
    
    if not offers:
        return f"No external vendors found for '{full_name}'."
        
    report = f"📊 Market Analysis for '{full_name}' (Sorted by Price):\n"
    for i, o in enumerate(offers):
        v_name, price, days, reliability, endpoint = o
        report += (f"{i+1}. VENDOR: {v_name}\n"
                   f"   Price: ${price:.2f} | Delivery: {days} days | Reliability: {reliability}\n"
                   f"   Endpoint: {endpoint}\n")
        
    return report

# --- 2. The A2A Negotiation Tool (External Action) ---

async def negotiate_with_vendor(vendor_endpoint: str, product: str, offer_price: float, quantity: int) -> str:
    """
    Dynamically connects to a Remote Vendor Agent via A2A to place an order.
    """
    print(f"\n🔄 [A2A] Initiating Handshake with {vendor_endpoint}...")
    
    card_url = f"{vendor_endpoint.rstrip('/')}/.well-known/agent-card.json"
    
    try:
        remote_agent = RemoteA2aAgent(
            name="dynamic_vendor_client",
            agent_card=card_url
        )
        
        message = (f"PURCHASE ORDER REQUEST:\n"
                   f"Item: {product}\n"
                   f"Quantity: {quantity}\n"
                   f"Target Price: ${offer_price}\n"
                   f"Please confirm if you accept this offer.")
        
        temp_session = InMemorySessionService()
        
        # Ensure session exists for the A2A sub-call
        await temp_session.create_session(
            app_name="procurement_negotiation_task",
            user_id="procurement_bot",
            session_id="txn_001"
        )

        runner = Runner(
            agent=remote_agent, 
            session_service=temp_session,
            app_name="procurement_negotiation_task"
        )
        
        print(f"📨 [A2A] Sending Offer: {quantity}x {product} @ ${offer_price}...")
        
        response_text = "No response from vendor."
        
        async for event in runner.run_async(
            user_id="procurement_bot", 
            session_id="txn_001", 
            new_message=types.Content(parts=[types.Part(text=message)])
        ):
            if event.is_final_response():
                response_text = event.content.parts[0].text
        
        print(f"Tb [A2A] Vendor Replied: {response_text}")
        return f"VENDOR RESPONSE:\n{response_text}"

    except Exception as e:
        return f"❌ A2A Connection Failed: {str(e)}"

# --- 3. The Agent Definition (With PlanReActPlanner) ---

def create_procurement_agent():
    """
    Creates the Procurement Agent using the PlanReActPlanner.
    """
    # We use the Pro model for the planner so it can reason effectively
    model_config = Gemini(
        model="gemini-2.5-pro",
        retry_options=types.HttpRetryOptions(attempts=3)
    )
    
    system_instruction = """
    You are the Senior Buyer for VeganFlow. 
    
    GOAL: Secure inventory at the lowest cost.
    
    STRATEGY:
    1. OBSERVATION: Call 'get_vendor_options' to see the market sorted by price.
    2. REASONING: Call 'load_memory' to check our historical target price.
    3. PLANNING: 
       - Start with the cheapest vendor. 
       - Offer 10% below their list price.
    4. EXECUTION: Call 'negotiate_with_vendor'.
    5. ADAPTATION (CRITICAL): 
       - IF Accepted: Stop.
       - IF Rejected with a Counter-Offer: 
           - COMPARE the Counter-Offer to the List Price of the NEXT vendor.
           - IF Counter-Offer < Next Vendor's Price -> ACCEPT the Counter-Offer (Call negotiate again with that price).
           - IF Counter-Offer > Next Vendor's Price -> Move to the NEXT vendor.
           - Do not stop until you have a deal or run out of vendors.
    """

    return LlmAgent(
        name="procurement_negotiator",
        model=model_config,
        instruction=system_instruction,
        tools=[get_vendor_options, negotiate_with_vendor, load_memory],
        # planner=PlanReActPlanner()
    )

# --- 4. Local Test Block ---
if __name__ == "__main__":
    async def test_negotiation():
        print("🧪 Starting Procurement Agent Test (With ReAct Planner)...")
        
        # 1. Setup Memory
        memory_service = InMemoryMemoryService()
        
        # 2. Seed Strategy
        print("🧠 Seeding Strategy into Memory...")
        
        seeder_agent = LlmAgent(
            name="memory_seeder",
            model=Gemini(model="gemini-2.0-flash"),
            instruction="You are a scribe."
        )
        
        session_service = InMemorySessionService()
        seed_user_id = "test_user"
        seed_session_id = "seed_session_01"
        
        await session_service.create_session(
            app_name="seeder_app", 
            user_id=seed_user_id, 
            session_id=seed_session_id
        )
        
        seeder_runner = Runner(
            agent=seeder_agent,
            session_service=session_service,
            app_name="seeder_app"
        )
        
        strategy_text = "Strategic Goal: For 'Oat Barista Blend', target price is $3.30."
        
        async for _ in seeder_runner.run_async(
            user_id=seed_user_id,
            session_id=seed_session_id,
            new_message=types.Content(parts=[types.Part(text=strategy_text)])
        ):
            pass
            
        seed_session = await session_service.get_session(
            app_name="seeder_app", 
            user_id=seed_user_id, 
            session_id=seed_session_id
        )
        await memory_service.add_session_to_memory(seed_session)
        print("✅ Strategy Ingested.")

        # 3. Initialize Procurement Agent
        agent = create_procurement_agent()
        
        # Ensure the test session exists for the runner
        await session_service.create_session(
            app_name="procurement_test", 
            user_id=seed_user_id, 
            session_id="test_session_01"
        )
        
        runner = Runner(
            agent=agent, 
            session_service=session_service, 
            memory_service=memory_service,
            app_name="procurement_test"
        )
        
        # 4. Run the Test
        query = "Find vendors for 'Oat Barista Blend' and get me a deal. Don't stop until you check everyone!"
        
        print(f"\n👤 User: {query}\n")
        
        async for event in runner.run_async(
            user_id=seed_user_id, 
            session_id="test_session_01", 
            new_message=types.Content(parts=[types.Part(text=query)])
        ):
            if event.is_final_response():
                print(f"\n🤖 Agent Final Decision:\n{event.content.parts[0].text}")

    asyncio.run(test_negotiation())
