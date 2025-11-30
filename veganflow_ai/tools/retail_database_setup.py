import sqlite3
import datetime

def setup_retail_database():
    """
    Creates the 'VeganFlow' POS database with the COMPLETE VENDOR ECOSYSTEM.
    
    Schema:
    1. products: Internal inventory status (Stock, Sales Velocity).
    2. vendors: The directory of external agents (A2A Endpoints).
    3. vendor_offers: The marketplace data (Prices, Delivery Times).
    """
    db_name = 'veganflow_store.db'
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # --- 1. Clean Slate (Drop old tables) ---
    cursor.execute('DROP TABLE IF EXISTS products')
    cursor.execute('DROP TABLE IF EXISTS vendors')
    cursor.execute('DROP TABLE IF EXISTS vendor_offers') 

    # --- 2. Create Schema ---
    
    # Internal Inventory (Must match agents/inventory.py SQL structure)
    cursor.execute('''
    CREATE TABLE products (
        product_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        stock_quantity INTEGER NOT NULL,
        sales_velocity_daily INTEGER NOT NULL,
        target_stock_level INTEGER NOT NULL,
        vendor_id TEXT NOT NULL
    )
    ''')

    # External Agent Directory
    cursor.execute('''
    CREATE TABLE vendors (
        vendor_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL, 
        reliability_score REAL, 
        contact_endpoint TEXT NOT NULL
    )
    ''')

    # Market Data (The "Competition")
    cursor.execute('''
    CREATE TABLE vendor_offers (
        offer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id TEXT,
        vendor_id TEXT,
        price_wholesale REAL,
        min_order_qty INTEGER,
        delivery_days INTEGER,
        batch_expiry_date DATE,
        FOREIGN KEY(product_id) REFERENCES products(product_id),
        FOREIGN KEY(vendor_id) REFERENCES vendors(vendor_id)
    )
    ''')

    # --- 3. Seed Vendors (11 Agents - Unchanged) ---
    vendors = [
        ('V-01', 'Earthly Gourmet', 'Distributor', 0.98, 'http://localhost:8001'),
        ('V-02', 'Feesers Food Dst', 'Distributor', 0.92, 'http://localhost:8002'),
        ('V-03', 'Clark Distributing', 'Distributor', 0.88, 'http://localhost:8003'),
        ('V-04', 'LCG Foods', 'Distributor', 0.95, 'http://localhost:8004'),
        ('V-05', 'Miyokos Creamery', 'Maker', 0.99, 'http://localhost:8005'),
        ('V-06', 'Rebel Cheese', 'Maker', 0.96, 'http://localhost:8006'),
        ('V-07', 'Treeline Cheese', 'Maker', 0.94, 'http://localhost:8007'),
        ('V-08', 'The Vreamery', 'Aggregator', 0.97, 'http://localhost:8008'),
        ('V-09', 'The BE Hive', 'Specialist', 0.93, 'http://localhost:8009'),
        ('V-10', 'All Vegetarian Inc', 'Specialist', 0.85, 'http://localhost:8010'),
        ('V-11', 'FakeMeats.com', 'Aggregator', 0.99, 'http://localhost:8011')
    ]

    # --- 4. Seed Products (Expanded to 20+ Products - FIXED INSERTION) ---
    today = datetime.date.today()

    products = [
        # BEVERAGES & DAIRY ALTERNATIVES (High Velocity/Commodity)
        ('P-OAT1', 'Oat Barista Blend', 'Beverage', 12, 15, 100, 'V-01'),      # CRITICAL STOCKOUT (12/15 = 0.8 days left)
        ('P-OAT2', 'Almond Milk Unsweet', 'Beverage', 45, 5, 50, 'V-04'),
        ('P-DAI', 'Soy Yogurt (Plain)', 'Dairy-Alt', 30, 3, 40, 'V-02'),
        ('P-CREAM', 'Cultured Cashew Creamer', 'Dairy-Alt', 15, 2, 30, 'V-05'), # Maker Direct

        # ARTISANAL CHEESE (High Value/Short Expiry)
        ('P-BRIE', 'Cultured Truffle Brie', 'Cheese', 8, 2, 20, 'V-06'),       # WASTE RISK
        ('P-CHED', 'Aged Pepper Jack Block', 'Cheese', 35, 4, 50, 'V-05'),
        ('P-SMOK', 'Smoked Gouda Style Wheel', 'Cheese', 15, 1, 30, 'V-07'),
        
        # FRESH/PRODUCE (Perishable)
        ('P-KALE', 'Local Organic Kale', 'Produce', 5, 1, 10, 'V-08'),
        ('P-TEM', 'Artisanal Tempeh Batch', 'Produce', 10, 2, 20, 'V-09'),
        ('P-FERM', 'Kimchi - Small Batch', 'Produce', 25, 3, 30, 'V-08'),

        # MEAT ALTERNATIVES (Bulk/Specialist)
        ('P-PEP', 'Seitan Pepperoni (Bulk)', 'Deli', 40, 8, 100, 'V-09'),
        ('P-SAUS', 'Beyond Sausage Links', 'Deli', 80, 10, 150, 'V-02'),
        ('P-BEHI', 'Chorizo Seitan', 'Deli', 50, 5, 75, 'V-09'),
        ('P-FISH', 'Vegan Jumbo Shrimp', 'Frozen', 5, 1, 20, 'V-10'),          # CRITICAL LOW

        # FROZEN & READY-TO-EAT
        ('P-PIZ', 'Frozen Margherita Pizza', 'Frozen', 120, 15, 200, 'V-04'),
        ('P-MAC', 'Frozen Mac & Cheese', 'Frozen', 90, 10, 150, 'V-02'),
        ('P-FAL', 'Falafel Mix Dry', 'Pantry', 30, 5, 50, 'V-03'),

        # PANTRY STAPLES (Low Velocity/High Target)
        ('P-MAY', 'Vegan Mayo Large', 'Pantry', 25, 2, 50, 'V-01'),
        ('P-TUNA', 'Plant-Based Tuna Cans', 'Pantry', 150, 10, 300, 'V-04'),
        ('P-COOK', 'Gluten-Free Cookies', 'Pantry', 50, 4, 80, 'V-11'),
        ('P-SLAW', 'Ready-Mix Coleslaw', 'Produce', 25, 5, 40, 'V-08')
    ]

    # --- 5. Seed Offers (The Competition) ---
    fresh = today + datetime.timedelta(days=120)
    clearance = today + datetime.timedelta(days=15) # Riskier, cheaper stock
    
    offers = [
        # SCENARIO A: Oat Milk War (V-01, V-03, V-04 compete on speed/price)
        ('P-OAT1', 'V-01', 3.50, 12, 2, fresh),  # Standard Price/Speed (Earthly)
        ('P-OAT1', 'V-03', 3.25, 50, 5, fresh),  # Cheapest/Slowest (Clark)
        ('P-OAT1', 'V-04', 3.80, 6, 1, fresh),   # Fastest/Most Expensive (LCG)

        # SCENARIO B: Cheese Competition (Maker vs Aggregator)
        ('P-BRIE', 'V-06', 9.50, 10, 4, fresh),  # Rebel Cheese (Direct Maker)
        ('P-BRIE', 'V-08', 11.00, 1, 2, fresh),  # The Vreamery (Aggregator Markup, but fast)
        ('P-SMOK', 'V-07', 8.90, 15, 3, fresh),  # Treeline Cheese

        # SCENARIO C: Bulk/Meat Alternatives (Specialist vs Clearance)
        ('P-PEP', 'V-09', 12.00, 5, 3, fresh),   # The BE Hive (Specialist Price)
        ('P-PEP', 'V-11', 8.50, 20, 2, clearance), # FakeMeats (Clearance/Expiry Risk)

        # SCENARIO D: Frozen Goods
        ('P-FISH', 'V-10', 14.00, 10, 7, fresh), # All Vegetarian Inc. (Slow shipping/high reliability)
        ('P-FISH', 'V-02', 14.50, 20, 3, fresh), # Feeser's (Faster shipping/higher price)
        
        # SCENARIO E: Standard Stock
        ('P-TUNA', 'V-04', 5.50, 50, 2, fresh),
        ('P-TUNA', 'V-03', 5.30, 100, 4, fresh),
        ('P-COOK', 'V-11', 4.10, 20, 1, fresh),
        ('P-MAC', 'V-02', 7.90, 50, 3, fresh),
        ('P-PIZ', 'V-04', 9.20, 10, 1, fresh),
        ('P-SLAW', 'V-08', 3.50, 5, 2, fresh)
    ]

    # --- 6. Execute Insertions ---
    # The number of '?' marks must match the number of columns in the CREATE TABLE statements.
    cursor.executemany('INSERT INTO vendors VALUES (?,?,?,?,?)', vendors)
    cursor.executemany('INSERT INTO products VALUES (?,?,?,?,?,?,?)', products)
    cursor.executemany('INSERT INTO vendor_offers (product_id, vendor_id, price_wholesale, min_order_qty, delivery_days, batch_expiry_date) VALUES (?,?,?,?,?,?)', offers)

    conn.commit()
    print(f"✅ Database '{db_name}' rebuilt with {len(products)} products and {len(offers)} competing offers.")
    print("   - CRITICAL SCENARIO: Oat Barista Blend has 0.8 days supply.")
    conn.close()

if __name__ == "__main__":
    setup_retail_database()
