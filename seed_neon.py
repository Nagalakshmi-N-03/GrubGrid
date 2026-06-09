"""
seed_neon.py
Seeds Neon database with restaurants, menu items, orders and competitor prices.
"""

import psycopg2
import random
import uuid
from datetime import datetime, timedelta

NEON_CONN_STR = "postgresql://neondb_owner:npg_2JvT7gUCOMSy@ep-rapid-darkness-ao16vhgr-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

conn = psycopg2.connect(NEON_CONN_STR)
cur  = conn.cursor()

# ─── Restaurants ──────────────────────────────────────────
print("Seeding restaurants...")
cur.execute("""
INSERT INTO restaurants (restaurant_id, restaurant_name, location, cuisine_type) VALUES
('r001','Spice Garden','Anna Nagar','Indian'),
('r002','Burger Barn','T. Nagar','Fast Food'),
('r003','Pizza Palace','Adyar','Italian'),
('r004','Dosa Delight','Tambaram','South Indian'),
('r005','Noodle House','Perambur','Chinese'),
('r006','Biryani Bros','Nungambakkam','Biryani'),
('r007','Wrap Republic','Mylapore','Mediterranean'),
('r008','Curry Corner','Velachery','Indian')
ON CONFLICT DO NOTHING;
""")

# ─── Menu Items ───────────────────────────────────────────
print("Seeding menu items...")
cur.execute("""
INSERT INTO menu_items (item_id, restaurant_id, item_name, category, price) VALUES
('m001','r001','Paneer Butter Masala','Main',220),
('m002','r001','Dal Tadka','Main',150),
('m003','r001','Garlic Naan','Bread',40),
('m004','r002','Classic Burger','Burger',180),
('m005','r002','Cheese Fries','Sides',120),
('m006','r002','Chicken Wrap','Wrap',200),
('m007','r003','Margherita Pizza','Pizza',280),
('m008','r003','Pepperoni Pizza','Pizza',320),
('m009','r003','Garlic Bread','Sides',90),
('m010','r004','Masala Dosa','Dosa',100),
('m011','r004','Rava Idli','Breakfast',80),
('m012','r004','Filter Coffee','Beverage',40),
('m013','r005','Veg Noodles','Noodles',160),
('m014','r005','Chicken Fried Rice','Rice',200),
('m015','r005','Manchurian','Starter',140),
('m016','r006','Chicken Biryani','Biryani',260),
('m017','r006','Mutton Biryani','Biryani',320),
('m018','r006','Raita','Sides',50),
('m019','r007','Falafel Wrap','Wrap',190),
('m020','r007','Shawarma','Wrap',170),
('m021','r007','Hummus Plate','Starter',150),
('m022','r008','Butter Chicken','Main',280),
('m023','r008','Palak Paneer','Main',240),
('m024','r008','Jeera Rice','Rice',100)
ON CONFLICT DO NOTHING;
""")

# ─── Raw Orders (30 days of history) ─────────────────────
print("Seeding raw orders...")
restaurants = [
    ("r001","Spice Garden"), ("r002","Burger Barn"), ("r003","Pizza Palace"),
    ("r004","Dosa Delight"), ("r005","Noodle House"), ("r006","Biryani Bros"),
    ("r007","Wrap Republic"), ("r008","Curry Corner"),
]
menu = [
    ("m001","r001","Paneer Butter Masala",220), ("m002","r001","Dal Tadka",150), ("m003","r001","Garlic Naan",40),
    ("m004","r002","Classic Burger",180), ("m005","r002","Cheese Fries",120), ("m006","r002","Chicken Wrap",200),
    ("m007","r003","Margherita Pizza",280), ("m008","r003","Pepperoni Pizza",320), ("m009","r003","Garlic Bread",90),
    ("m010","r004","Masala Dosa",100), ("m011","r004","Rava Idli",80), ("m012","r004","Filter Coffee",40),
    ("m013","r005","Veg Noodles",160), ("m014","r005","Chicken Fried Rice",200), ("m015","r005","Manchurian",140),
    ("m016","r006","Chicken Biryani",260), ("m017","r006","Mutton Biryani",320), ("m018","r006","Raita",50),
    ("m019","r007","Falafel Wrap",190), ("m020","r007","Shawarma",170), ("m021","r007","Hummus Plate",150),
    ("m022","r008","Butter Chicken",280), ("m023","r008","Palak Paneer",240), ("m024","r008","Jeera Rice",100),
]
locations = ["Anna Nagar","T. Nagar","Adyar","Velachery","Porur","Tambaram","Perambur","Mylapore","Nungambakkam","Chromepet"]
statuses  = ["placed","preparing","out_for_delivery","delivered"]

orders = []
for item_id, restaurant_id, item_name, price in menu:
    restaurant_name = next(r[1] for r in restaurants if r[0] == restaurant_id)
    for _ in range(20):
        qty        = random.randint(1, 4)
        placed_at  = datetime.utcnow() - timedelta(days=random.uniform(0, 30))
        orders.append((
            str(uuid.uuid4()), restaurant_id, restaurant_name,
            item_id, item_name, qty, price, price * qty,
            f"C{random.randint(1000,9999)}", random.choice(locations),
            random.choice(statuses), placed_at, None
        ))

cur.executemany("""
    INSERT INTO raw_orders (
        order_id, restaurant_id, restaurant_name,
        item_id, item_name, quantity, unit_price, total_price,
        customer_id, location, status, placed_at, delivered_at
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT DO NOTHING;
""", orders)
print(f"  {len(orders)} orders inserted.")

# ─── Competitor Prices ────────────────────────────────────
print("Seeding competitor prices...")
competitors = ["Swiggy", "Zomato", "MagicPin"]
price_records = []
for competitor in competitors:
    for item_id, restaurant_id, item_name, our_price in menu:
        restaurant_name  = next(r[1] for r in restaurants if r[0] == restaurant_id)
        variation        = random.uniform(-0.20, 0.20)
        competitor_price = round(our_price * (1 + variation), 2)
        price_gap        = round(our_price - competitor_price, 2)
        is_undercut      = competitor_price < our_price
        price_records.append((
            datetime.utcnow(), competitor, restaurant_name,
            item_name, competitor_price, our_price, price_gap, is_undercut
        ))

cur.executemany("""
    INSERT INTO competitor_prices (
        scraped_at, competitor_name, restaurant_name,
        item_name, competitor_price, our_price, price_gap, is_undercut
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);
""", price_records)
print(f"  {len(price_records)} price records inserted.")

conn.commit()
conn.close()
print("\n✅ Neon seeding complete!")