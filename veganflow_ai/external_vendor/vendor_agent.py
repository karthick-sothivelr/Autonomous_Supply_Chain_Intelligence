import argparse
import uvicorn
import sys
import logging
import re
from dotenv import load_dotenv  
load_dotenv()

# Configure logging to suppress noisy access logs during the demo
logging.basicConfig(level=logging.WARNING)

from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.models.google_llm import Gemini
from google.genai import types

def create_vendor_agent(name: str, reliability: float, port: int):
    """
    Creates a simulated Vendor Agent with a specific 'personality'.
    """
    # Use Flash for the vendor to keep the simulation fast and cheap
    model_config = Gemini(model="gemini-2.0-flash-lite") 

    # --- The Negotiation Logic ---
    def check_quote(product_name: str, quantity: int, offer_price: float) -> str:
        """
        Evaluates an incoming purchase offer using a realistic price catalog.
        """
        print(f"\n[VENDOR: {name}] 🔔 Incoming Offer: {quantity}x {product_name} @ ${offer_price}")
        
        # --- FIX: Realistic Market Prices (Matching our DB) ---
        # In a real app, this would query the vendor's internal ERP.
        MARKET_PRICES = {
            "Oat Barista Blend": 3.50,       # Matches V-01 in DB
            "Cultured Truffle Brie": 10.00,  # Matches V-06 in DB
            "Seitan Pepperoni": 12.00,       # Matches V-09 in DB
            "Vegan Jumbo Shrimp": 14.00,
            "Texas BBQ Soy Jerky": 5.00
        }

        # Default to 10.0 if product not found (Fuzzy match)
        base_market_price = 10.0
        for key, price in MARKET_PRICES.items():
            if key in product_name:
                base_market_price = price
                break

        # Logic: Reliability affects the "floor price".
        # High reliability (0.98) = Stricter margins (Floor is 98% of market).
        # Low reliability (0.85) = More desperate (Floor is 85% of market).
        min_acceptable_price = base_market_price * reliability 
        
        # Bulk Discount Logic: If buying > 50 units, lower the floor by 5%
        if quantity > 50:
            min_acceptable_price *= 0.95
            print(f"[{name}] Bulk discount logic applied (Floor: ${min_acceptable_price:.2f}).")

        # Decision Time
        if offer_price >= min_acceptable_price:
            days = int((1 / reliability) * 2) 
            return f"ACCEPTED: We can supply {quantity} units of {product_name} at ${offer_price}. Delivery in {days} days."
        
        # Counter-Offer: 5% above their floor
        counter_offer = round(min_acceptable_price * 1.05, 2)
        return f"REJECTED: Price too low. The lowest we can go is ${counter_offer}. Take it or leave it."

    # --- Agent Definition ---
    
    safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())

    agent = LlmAgent(
        name=safe_name,
        model=model_config,
        description=f"Automated Sales Agent for {name}",
        instruction=f"""
        You are the Sales Representative for {name}.
        Your Reliability Score is {reliability}.
        
        Your goal is to sell products but maintain margins.
        You MUST use the 'check_quote' tool to validate every offer. 
        Do not hallucinate an acceptance if the tool returns REJECTED.
        Be concise and transactional.
        """,
        tools=[check_quote]
    )
    
    return to_a2a(agent, port=port)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", type=str, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--reliability", type=float, default=0.9)
    args = parser.parse_args()

    print(f"🚀 Vendor '{args.name}' online at http://localhost:{args.port} (Reliability: {args.reliability})")
    
    app = create_vendor_agent(args.name, args.reliability, args.port)
    uvicorn.run(app, host="localhost", port=args.port, log_level="warning")
