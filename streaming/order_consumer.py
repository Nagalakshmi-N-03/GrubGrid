"""
order_consumer.py
Reads live order messages from Kafka topic and writes them to PostgreSQL.
Runs continuously — restart it if it crashes.
"""

import json
import os
import psycopg2
import psycopg2.extras
from kafka import KafkaConsumer
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# ─── Config ───────────────────────────────────────────────
KAFKA_BROKER    = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC     = os.getenv("KAFKA_TOPIC", "live_orders")
KAFKA_GROUP_ID  = "grubgrid_order_consumer"

POSTGRES_HOST   = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT   = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB     = os.getenv("POSTGRES_DB", "grubgrid")
POSTGRES_USER   = os.getenv("POSTGRES_USER", "grubgrid_user")
POSTGRES_PASS   = os.getenv("POSTGRES_PASSWORD", "grubgrid_pass")


# ─── Database ─────────────────────────────────────────────
def get_db_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASS,
    )


def insert_order(conn, order: dict):
    sql = """
        INSERT INTO raw_orders (
            order_id, restaurant_id, restaurant_name,
            item_id, item_name, quantity,
            unit_price, total_price,
            customer_id, location, status,
            placed_at, delivered_at
        ) VALUES (
            %(order_id)s, %(restaurant_id)s, %(restaurant_name)s,
            %(item_id)s, %(item_name)s, %(quantity)s,
            %(unit_price)s, %(total_price)s,
            %(customer_id)s, %(location)s, %(status)s,
            %(placed_at)s, %(delivered_at)s
        )
        ON CONFLICT (order_id) DO NOTHING;
    """
    with conn.cursor() as cur:
        cur.execute(sql, order)
    conn.commit()


# ─── Consumer ─────────────────────────────────────────────
def create_consumer():
    return KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        group_id=KAFKA_GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
        consumer_timeout_ms=-1,   # block forever — keep listening
    )


def run_consumer():
    print(f"🎧 GrubGrid Order Consumer starting...")
    print(f"   Broker   : {KAFKA_BROKER}")
    print(f"   Topic    : {KAFKA_TOPIC}")
    print(f"   Group ID : {KAFKA_GROUP_ID}\n")

    conn     = get_db_connection()
    consumer = create_consumer()
    count    = 0

    print("⏳ Waiting for messages...\n")

    try:
        for message in consumer:
            order = message.value
            count += 1

            try:
                insert_order(conn, order)
                print(f"💾 #{count} Saved → {order['order_id'][:8]}... | "
                      f"{order['restaurant_name']} | "
                      f"{order['item_name']} | "
                      f"₹{order['total_price']} | "
                      f"{order['status']}")

            except psycopg2.OperationalError:
                # reconnect if DB connection drops
                print("🔁 DB connection lost — reconnecting...")
                conn = get_db_connection()
                insert_order(conn, order)

            except Exception as e:
                print(f"❌ Failed to insert order {order.get('order_id')}: {e}")
                conn.rollback()

    except KeyboardInterrupt:
        print(f"\n⛔ Consumer stopped. Total orders saved: {count}")
    finally:
        consumer.close()
        conn.close()


if __name__ == "__main__":
    run_consumer()