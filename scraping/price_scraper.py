"""
price_scraper.py
Simulates scraping competitor restaurant menu prices.
In a real scenario this would scrape public pages on Swiggy/Zomato.
Here we simulate realistic scraped data since scraping live sites
requires dynamic URLs and login — not suitable for a portfolio project.
"""

import os
import random
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─── Config ───────────────────────────────────────────────
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB   = os.getenv("POSTGRES_DB", "grubgrid")
POSTGRES_USER = os.getenv("POSTGRES_USER", "grubgrid_user")
POSTGRES_PASS = os.getenv("POSTGRES_PASSWORD", "grubgrid_pass")

# ─── Our Platform's Menu Prices ───────────────────────────
# This represents GrubGrid's own menu — the baseline for comparison
OUR_MENU = [
    {"restaurant": "Spice Garden",  "item": "Paneer Butter Masala", "our_price": 220},
    {"restaurant": "Spice Garden",  "item": "Dal Tadka",            "our_price": 150},
    {"restaurant": "Spice Garden",  "item": "Garlic Naan",          "our_price": 40},
    {"restaurant": "Burger Barn",   "item": "Classic Burger",       "our_price": 180},
    {"restaurant": "Burger Barn",   "item": "Cheese Fries",         "our_price": 120},
    {"restaurant": "Burger Barn",   "item": "Chicken Wrap",         "our_price": 200},
    {"restaurant": "Pizza Palace",  "item": "Margherita Pizza",     "our_price": 280},
    {"restaurant": "Pizza Palace",  "item": "Pepperoni Pizza",      "our_price": 320},
    {"restaurant": "Pizza Palace",  "item": "Garlic Bread",         "our_price": 90},
    {"restaurant": "Dosa Delight",  "item": "Masala Dosa",          "our_price": 100},
    {"restaurant": "Dosa Delight",  "item": "Rava Idli",            "our_price": 80},
    {"restaurant": "Dosa Delight",  "item": "Filter Coffee",        "our_price": 40},
    {"restaurant": "Noodle House",  "item": "Veg Noodles",          "our_price": 160},
    {"restaurant": "Noodle House",  "item": "Chicken Fried Rice",   "our_price": 200},
    {"restaurant": "Noodle House",  "item": "Manchurian",           "our_price": 140},
    {"restaurant": "Biryani Bros",  "item": "Chicken Biryani",      "our_price": 260},
    {"restaurant": "Biryani Bros",  "item": "Mutton Biryani",       "our_price": 320},
    {"restaurant": "Biryani Bros",  "item": "Raita",                "our_price": 50},
    {"restaurant": "Wrap Republic", "item": "Falafel Wrap",         "our_price": 190},
    {"restaurant": "Wrap Republic", "item": "Shawarma",             "our_price": 170},
    {"restaurant": "Wrap Republic", "item": "Hummus Plate",         "our_price": 150},
    {"restaurant": "Curry Corner",  "item": "Butter Chicken",       "our_price": 280},
    {"restaurant": "Curry Corner",  "item": "Palak Paneer",         "our_price": 240},
    {"restaurant": "Curry Corner",  "item": "Jeera Rice",           "our_price": 100},
]

# ─── Competitor Sources ───────────────────────────────────
COMPETITORS = ["Swiggy", "Zomato", "MagicPin"]


def simulate_scraped_price(our_price: float) -> float:
    """
    Simulates a competitor price by applying a random variation.
    ~40% chance competitor undercuts, ~60% chance they're higher or same.
    """
    variation = random.choice([
        random.uniform(-0.20, -0.05),   # undercut by 5–20%
        random.uniform(-0.20, -0.05),   # undercut (weighted higher)
        random.uniform(0.00,  0.15),    # same or slightly higher
        random.uniform(0.05,  0.25),    # noticeably higher
        random.uniform(-0.03,  0.03),   # nearly same
    ])
    scraped = round(our_price * (1 + variation), 2)
    return max(scraped, 10.0)           # floor at ₹10


def scrape_competitor_prices() -> list[dict]:
    """
    Simulates scraping prices from all competitors for all menu items.
    Returns a list of price comparison records.
    """
    results = []
    scraped_at = datetime.utcnow()

    for competitor in COMPETITORS:
        print(f"\n🌐 Scraping {competitor}...")
        for menu_item in OUR_MENU:
            competitor_price = simulate_scraped_price(menu_item["our_price"])
            price_gap        = round(menu_item["our_price"] - competitor_price, 2)
            is_undercut      = competitor_price < menu_item["our_price"]

            record = {
                "scraped_at":        scraped_at,
                "competitor_name":   competitor,
                "restaurant_name":   menu_item["restaurant"],
                "item_name":         menu_item["item"],
                "competitor_price":  competitor_price,
                "our_price":         menu_item["our_price"],
                "price_gap":         price_gap,
                "is_undercut":       is_undercut,
            }
            results.append(record)

            status = "🔴 UNDERCUT" if is_undercut else "🟢 OK"
            print(f"   {status} | {menu_item['restaurant']} | {menu_item['item']} | "
                  f"Ours: ₹{menu_item['our_price']} | "
                  f"{competitor}: ₹{competitor_price} | "
                  f"Gap: ₹{price_gap}")

    return results


def save_to_postgres(records: list[dict]):
    conn = psycopg2.connect(
        host=POSTGRES_HOST, port=POSTGRES_PORT,
        dbname=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASS
    )
    sql = """
        INSERT INTO competitor_prices (
            scraped_at, competitor_name, restaurant_name,
            item_name, competitor_price, our_price,
            price_gap, is_undercut
        ) VALUES (
            %(scraped_at)s, %(competitor_name)s, %(restaurant_name)s,
            %(item_name)s, %(competitor_price)s, %(our_price)s,
            %(price_gap)s, %(is_undercut)s
        );
    """
    with conn.cursor() as cur:
        for record in records:
            cur.execute(sql, record)
    conn.commit()
    conn.close()
    print(f"\n💾 Saved {len(records)} price records to PostgreSQL.")


def run_scraper():
    print("🕷️  GrubGrid Price Scraper starting...")
    print(f"   Competitors : {', '.join(COMPETITORS)}")
    print(f"   Menu items  : {len(OUR_MENU)}\n")

    records = scrape_competitor_prices()
    save_to_postgres(records)

    undercut_count = sum(1 for r in records if r["is_undercut"])
    print(f"\n📊 Summary:")
    print(f"   Total records scraped : {len(records)}")
    print(f"   Items being undercut  : {undercut_count}")
    print(f"   Scrape complete ✅")


if __name__ == "__main__":
    run_scraper()