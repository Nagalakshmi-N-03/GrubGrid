"""
price_comparator.py
Reads competitor_prices from PostgreSQL and produces a clean
comparison report — used by both the Streamlit alert app and Airflow DAG.
"""

import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# ─── Config ───────────────────────────────────────────────
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB   = os.getenv("POSTGRES_DB", "grubgrid")
POSTGRES_USER = os.getenv("POSTGRES_USER", "grubgrid_user")
POSTGRES_PASS = os.getenv("POSTGRES_PASSWORD", "grubgrid_pass")

UNDERCUT_THRESHOLD = 10.0   # alert if competitor is cheaper by ₹10+


def get_db_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST, port=POSTGRES_PORT,
        dbname=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASS,
        cursor_factory=psycopg2.extras.RealDictCursor
    )


def get_latest_scrape_time(conn) -> datetime:
    with conn.cursor() as cur:
        cur.execute("SELECT MAX(scraped_at) AS latest FROM competitor_prices;")
        row = cur.fetchone()
        return row["latest"]


def get_latest_comparison(conn) -> list[dict]:
    """Fetch all price records from the most recent scrape run."""
    sql = """
        SELECT
            competitor_name,
            restaurant_name,
            item_name,
            our_price,
            competitor_price,
            price_gap,
            is_undercut,
            scraped_at
        FROM competitor_prices
        WHERE scraped_at = (SELECT MAX(scraped_at) FROM competitor_prices)
        ORDER BY price_gap ASC;
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        return cur.fetchall()


def get_critical_undercuts(conn) -> list[dict]:
    """Items where competitor is cheaper by more than threshold."""
    sql = """
        SELECT
            competitor_name,
            restaurant_name,
            item_name,
            our_price,
            competitor_price,
            price_gap,
            scraped_at
        FROM competitor_prices
        WHERE scraped_at = (SELECT MAX(scraped_at) FROM competitor_prices)
          AND is_undercut = TRUE
          AND ABS(price_gap) >= %(threshold)s
        ORDER BY price_gap ASC;
    """
    with conn.cursor() as cur:
        cur.execute(sql, {"threshold": UNDERCUT_THRESHOLD})
        return cur.fetchall()


def get_summary_by_competitor(conn) -> list[dict]:
    """Count how many items each competitor undercuts."""
    sql = """
        SELECT
            competitor_name,
            COUNT(*) FILTER (WHERE is_undercut = TRUE)  AS items_undercut,
            COUNT(*)                                     AS total_items,
            ROUND(AVG(price_gap)::numeric, 2)            AS avg_price_gap
        FROM competitor_prices
        WHERE scraped_at = (SELECT MAX(scraped_at) FROM competitor_prices)
        GROUP BY competitor_name
        ORDER BY items_undercut DESC;
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        return cur.fetchall()


def get_summary_by_restaurant(conn) -> list[dict]:
    """Which restaurants are most undercut?"""
    sql = """
        SELECT
            restaurant_name,
            COUNT(*) FILTER (WHERE is_undercut = TRUE)  AS items_undercut,
            COUNT(*)                                     AS total_items
        FROM competitor_prices
        WHERE scraped_at = (SELECT MAX(scraped_at) FROM competitor_prices)
        GROUP BY restaurant_name
        ORDER BY items_undercut DESC;
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        return cur.fetchall()


def print_report():
    conn = get_db_connection()

    latest = get_latest_scrape_time(conn)
    print(f"\n📊 GrubGrid Price Comparison Report")
    print(f"   Latest scrape: {latest}\n")

    # ── Summary by competitor ──────────────────────────────
    print("─" * 60)
    print("🏆 Competitor Summary")
    print("─" * 60)
    for row in get_summary_by_competitor(conn):
        print(f"  {row['competitor_name']:10} | "
              f"Undercut: {row['items_undercut']:2}/{row['total_items']} items | "
              f"Avg gap: ₹{row['avg_price_gap']}")

    # ── Summary by restaurant ──────────────────────────────
    print("\n─" * 60)
    print("🍽️  Most Undercut Restaurants")
    print("─" * 60)
    for row in get_summary_by_restaurant(conn):
        print(f"  {row['restaurant_name']:15} | "
              f"Undercut on {row['items_undercut']}/{row['total_items']} items")

    # ── Critical alerts ───────────────────────────────────
    critical = get_critical_undercuts(conn)
    print(f"\n─" * 60)
    print(f"🚨 Critical Undercuts (gap ≥ ₹{UNDERCUT_THRESHOLD})")
    print("─" * 60)
    if critical:
        for row in critical:
            print(f"  🔴 {row['competitor_name']:10} | "
                  f"{row['restaurant_name']:15} | "
                  f"{row['item_name']:25} | "
                  f"Ours: ₹{row['our_price']} | "
                  f"Theirs: ₹{row['competitor_price']} | "
                  f"Gap: ₹{abs(row['price_gap'])}")
    else:
        print("  ✅ No critical undercuts found.")

    conn.close()


if __name__ == "__main__":
    print_report()