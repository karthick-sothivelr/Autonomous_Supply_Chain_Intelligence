import sqlite3
import os
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- 1. The Custom Database Tool ---

def query_inventory(query_type: str, product_name: str = None) -> str:
    """
    Directly queries the 'VeganFlow' POS database to check inventory health.
    
    Args:
        query_type: One of 'LOW_STOCK', 'EXPIRING_SOON', 'ALL', or 'PRODUCT_DETAIL'.
        product_name: The name of the product (required for 'PRODUCT_DETAIL').
        
    Returns:
        A text report of items matching the criteria.
    """
    # Connect to the local SQLite database
    conn = sqlite3.connect('veganflow_store.db')
    cursor = conn.cursor()
    
    results = []
    
    if query_type == 'LOW_STOCK':
        # Logic: Find items with < 3 days of supply (Stock / Daily Sales)
        sql = """
        SELECT name, stock_quantity, sales_velocity_daily, vendor_id 
        FROM products 
        WHERE (stock_quantity / sales_velocity_daily) < 3
        """
        cursor.execute(sql)
        items = cursor.fetchall()
        
        for item in items:
            name, stock, velocity, vendor = item
            days_left = round(stock / velocity, 1)
            results.append(
                f"🚨 CRITICAL STOCK: '{name}' has {stock} units. "
                f"Selling {velocity}/day. Stockout in {days_left} days. "
                f"Vendor: {vendor}"
            )

    elif query_type == 'EXPIRING_SOON':
        # Logic: Find items expiring in the next 7 days using the normalized vendor_offers table.
        sql = """
        SELECT p.name, p.stock_quantity, MIN(vo.batch_expiry_date) as expiry
        FROM products p
        JOIN vendor_offers vo ON p.product_id = vo.product_id
        GROUP BY p.product_id
        HAVING expiry < date('now', '+7 days')
        """
        cursor.execute(sql)
        items = cursor.fetchall()

        for item in items:
            name, stock, expiry = item
            results.append(
                f"⚠️ WASTE RISK: '{name}' expires on {expiry}. "
                f"{stock} units at risk."
            )

    elif query_type == 'ALL':
        # Return a detailed listing of all products including nearest expiry and available offers
        sql = """
        SELECT p.product_id, p.name, p.category, p.stock_quantity, p.sales_velocity_daily,
               p.target_stock_level, p.vendor_id,
               MIN(vo.batch_expiry_date) as nearest_expiry,
               GROUP_CONCAT(vo.vendor_id || ':' || vo.price_wholesale) as offers
        FROM products p
        LEFT JOIN vendor_offers vo ON p.product_id = vo.product_id
        GROUP BY p.product_id
        """
        cursor.execute(sql)
        items = cursor.fetchall()

        for item in items:
            product_id, name, category, stock, velocity, target, vendor_source = item[:7]
            nearest_expiry = item[7]
            offers = item[8] if item[8] is not None else 'N/A'

            results.append(
                f"Product ID: {product_id} | Name: {name} | Stock: {stock} / Target: {target} | Velocity/day: {velocity} | "
                f"Nearest Expiry: {nearest_expiry or 'N/A'} | Offers: {offers}"
            )

    elif query_type == 'PRODUCT_DETAIL':
        # NEW LOGIC: Retrieves full detail for a single product to inform a purchase decision
        if not product_name:
            return "Error: PRODUCT_DETAIL query requires 'product_name'."
        
        # Fuzzy match to find the product ID
        cursor.execute("SELECT product_id FROM products WHERE name LIKE ?", (f"%{product_name}%",))
        prod_id_res = cursor.fetchone()
        if not prod_id_res:
             return f"Error: Product '{product_name}' not found."

        product_id = prod_id_res[0]

        # Query all relevant data for the product (using a join)
        sql = """
        SELECT p.name, p.stock_quantity, p.sales_velocity_daily, p.target_stock_level,
               v.name as vendor_name, vo.price_wholesale, vo.delivery_days, vo.batch_expiry_date
        FROM products p
        LEFT JOIN vendor_offers vo ON p.product_id = vo.product_id
        LEFT JOIN vendors v ON vo.vendor_id = v.vendor_id
        WHERE p.product_id = ?
        ORDER BY vo.price_wholesale ASC
        """
        cursor.execute(sql, (product_id,))
        items = cursor.fetchall()

        if not items:
            return f"Product '{product_name}' found, but no offers available."

        # Format the detailed report
        header = f"--- DETAIL REPORT: {items[0][0]} ---\n"
        details = f"Inventory: {items[0][1]} / Target: {items[0][3]} | Velocity: {items[0][2]}/day\n\n"
        
        offers_list = []
        for item in items:
            vendor_name, price, days, expiry = item[4:]
            if vendor_name:
                 offers_list.append(f"VENDOR: {vendor_name} | Price: ${price} | Delivery: {days} days | Expiry: {expiry}")

        return header + details + "COMPETING OFFERS:\n" + "\n".join(offers_list)
        
    conn.close()
    
    if not results:
        return f"✅ No {query_type} issues found."
        
    return "\n".join(results)

# --- 2. The Agent Definition ---

def create_shelf_monitor():
    """
    Creates the Inventory Agent (The 'Eyes').
    Uses a custom function tool for direct database access.
    """
    model_config = Gemini(
        model="gemini-2.0-flash", # Flash is optimized for tool calling
        retry_options=types.HttpRetryOptions(attempts=3)
    )
    
    system_instruction = """
    You are the 'Shelf Monitor' for VeganFlow.
    Your job is to query the SQL database using your tools and report risks.
    
    TOOLS:
    - query_inventory(query_type, product_name): Use this to check the DB. Use 'LOW_STOCK' or 'EXPIRING_SOON' 
      for general risk checks. Use 'PRODUCT_DETAIL' if asked for specifics on one item before negotiating.
    
    LOGIC:
    1. If asked about "risks", "status", or "inventory", run BOTH 'LOW_STOCK' and 'EXPIRING_SOON' checks.
    2. If asked about a single item's purchase options, use 'PRODUCT_DETAIL'.
    3. Be precise.
    """
    
    return LlmAgent(
        name="shelf_monitor",
        model=model_config,
        instruction=system_instruction,
        tools=[query_inventory] # Register the custom function
    )

# --- 3. Local Test Block ---
if __name__ == "__main__":
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    import asyncio

    async def test_locally():
        print("🧪 Starting Local Test of Shelf Monitor Agent...")
        
        # 1. Define Constants
        APP_NAME = "shelf_monitor_test"
        SESSION_ID = "test_session_001"
        USER_ID = "test_user"

        # 2. Initialize Services
        agent = create_shelf_monitor()
        session_service = InMemorySessionService()
        
        # 3. FIX: Create Session with ALL required params (app_name, user_id, session_id)
        await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID
        )
        
        # 4. Initialize Runner
        runner = Runner(
            agent=agent, 
            session_service=session_service,
            app_name=APP_NAME 
        )
        
        # 5. Run the Test
        user_input = "Analyze our inventory risks."
        print(f"\n👤 User: {user_input}\n")
        
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=types.Content(parts=[types.Part(text=user_input)])
        ):
            if event.is_final_response():
                print(f"🤖 Agent Response:\n{event.content.parts[0].text}")

    asyncio.run(test_locally())
