"""
order_producer.py
Simulates live food orders being placed on the GrubGrid platform.
Publishes each order as a Kafka message every few seconds.
"""

import json
import time
import uuid
import random
from datetime import datetime
from kafka import KafkaProducer
from dotenv import load_dotenv
import os

load_dotenv()

# ─── Config ───────────────────────────────────────────────
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC  = os.getenv("KAFKA_TOPIC", "live_orders")
ORDER_INTERVAL_SECONDS = 2   # one order every 2 seconds

# ─── Sample Data ──────────────────────────────────────────
RESTAURANTS = [
    {"id": "R001", "name": "Spice Garden"},
    {"id": "R002", "name": "Burger Barn"},
    {"id": "R003", "name": "Pizza Palace"},
    {"id": "R004", "name": "Dosa Delight"},
    {"id": "R005", "name": "Noodle House"},
    {"id": "R006", "name": "Biryani Bros"},
    {"id": "R007", "name": "Wrap Republic"},
    {"id": "R008", "name": "Curry Corner"},
]

MENU_ITEMS = {
    "R001": [
        {"id": "M001", "name": "Paneer Butter Masala", "price": 220},
        {"id": "M002", "name": "Dal Tadka",            "price": 150},
        {"id": "M003", "name": "Garlic Naan",          "price": 40},
    ],
    "R002": [
        {"id": "M004", "name": "Classic Burger",       "price": 180},
        {"id": "M005", "name": "Cheese Fries",         "price": 120},
        {"id": "M006", "name": "Chicken Wrap",         "price": 200},
    ],
    "R003": [
        {"id": "M007", "name": "Margherita Pizza",     "price": 280},
        {"id": "M008", "name": "Pepperoni Pizza",      "price": 320},
        {"id": "M009", "name": "Garlic Bread",         "price": 90},
    ],
    "R004": [
        {"id": "M010", "name": "Masala Dosa",          "price": 100},
        {"id": "M011", "name": "Rava Idli",            "price": 80},
        {"id": "M012", "name": "Filter Coffee",        "price": 40},
    ],
    "R005": [
        {"id": "M013", "name": "Veg Noodles",          "price": 160},
        {"id": "M014", "name": "Chicken Fried Rice",   "price": 200},
        {"id": "M015", "name": "Manchurian",           "price": 140},
    ],
    "R006": [
        {"id": "M016", "name": "Chicken Biryani",      "price": 260},
        {"id": "M017", "name": "Mutton Biryani",       "price": 320},
        {"id": "M018", "name": "Raita",                "price": 50},
    ],
    "R007": [
        {"id": "M019", "name": "Falafel Wrap",         "price": 190},
        {"id": "M020", "name": "Shawarma",             "price": 170},
        {"id": "M021", "name": "Hummus Plate",         "price": 150},
    ],
    "R008": [
        {"id": "M022", "name": "Butter Chicken",       "price": 280},
        {"id": "M023", "name": "Palak Paneer",         "price": 240},
        {"id": "M024", "name": "Jeera Rice",           "price": 100},
    ],
}

LOCATIONS = [
    "Anna Nagar", "T. Nagar", "Adyar", "Velachery",
    "Porur", "Tambaram", "Perambur", "Mylapore",
    "Nungambakkam", "Chromepet"
]

STATUSES = ["placed", "preparing", "out_for_delivery", "delivered"]


# ─── Order Generator ──────────────────────────────────────
def generate_order():
    restaurant = random.choice(RESTAURANTS)
    items      = MENU_ITEMS[restaurant["id"]]
    item       = random.choice(items)
    quantity   = random.randint(1, 4)

    return {
        "order_id":        str(uuid.uuid4()),
        "restaurant_id":   restaurant["id"],
        "restaurant_name": restaurant["name"],
        "item_id":         item["id"],
        "item_name":       item["name"],
        "quantity":        quantity,
        "unit_price":      item["price"],
        "total_price":     round(item["price"] * quantity, 2),
        "customer_id":     f"C{random.randint(1000, 9999)}",
        "location":        random.choice(LOCATIONS),
        "status":          random.choice(STATUSES),
        "placed_at":       datetime.utcnow().isoformat(),
        "delivered_at":    None,
    }


# ─── Producer ─────────────────────────────────────────────
def create_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8"),
        retries=5,
        retry_backoff_ms=500,
    )


def on_send_success(record_metadata):
    print(f"  ✅ Sent → topic={record_metadata.topic} | "
          f"partition={record_metadata.partition} | "
          f"offset={record_metadata.offset}")


def on_send_error(excp):
    print(f"  ❌ Failed to send message: {excp}")


def run_producer():
    print(f"🚀 GrubGrid Order Producer starting...")
    print(f"   Broker : {KAFKA_BROKER}")
    print(f"   Topic  : {KAFKA_TOPIC}")
    print(f"   Interval: {ORDER_INTERVAL_SECONDS}s\n")

    producer = create_producer()
    order_count = 0

    try:
        while True:
            order = generate_order()
            order_count += 1

            print(f"📦 Order #{order_count} | {order['restaurant_name']} | "
                  f"{order['item_name']} x{order['quantity']} | "
                  f"₹{order['total_price']} | {order['location']} | {order['status']}")

            producer.send(
                KAFKA_TOPIC,
                key=order["order_id"],
                value=order
            ).add_callback(on_send_success).add_errback(on_send_error)

            producer.flush()
            time.sleep(ORDER_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print(f"\n⛔ Producer stopped. Total orders sent: {order_count}")
    finally:
        producer.close()


if __name__ == "__main__":
    run_producer()