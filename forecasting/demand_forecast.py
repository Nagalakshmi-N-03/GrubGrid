"""
demand_forecast.py
Runs Prophet demand forecasting on historical order data.
Predicts next 30 days demand per restaurant per menu item.
Stores forecast results back into PostgreSQL.
"""

import os
import warnings
import pandas as pd
import psycopg2
import psycopg2.extras
from datetime import datetime
from dotenv import load_dotenv

warnings.filterwarnings("ignore")

try:
    from prophet import Prophet
except ImportError:
    raise ImportError("Install prophet: pip install prophet")

load_dotenv()

# ─── Config ───────────────────────────────────────────────
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB   = os.getenv("POSTGRES_DB", "grubgrid")
POSTGRES_USER = os.getenv("POSTGRES_USER", "grubgrid_user")
POSTGRES_PASS = os.getenv("POSTGRES_PASSWORD", "grubgrid_pass")

FORECAST_DAYS        = 30
MIN_ROWS_FOR_FORECAST = 10   # skip items with too little history


# ─── Database ─────────────────────────────────────────────
def get_conn():
    return psycopg2.connect(
        host=POSTGRES_HOST, port=POSTGRES_PORT,
        dbname=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASS
    )


def ensure_forecast_table(conn):
    sql = """
        CREATE TABLE IF NOT EXISTS demand_forecasts (
            id                  SERIAL PRIMARY KEY,
            restaurant_id       VARCHAR(50),
            restaurant_name     VARCHAR(100),
            item_id             VARCHAR(50),
            item_name           VARCHAR(100),
            forecast_date       DATE,
            predicted_orders    NUMERIC(10, 2),
            lower_bound         NUMERIC(10, 2),
            upper_bound         NUMERIC(10, 2),
            is_peak_day         BOOLEAN,
            created_at          TIMESTAMP DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_forecast_date
            ON demand_forecasts(forecast_date);
        CREATE INDEX IF NOT EXISTS idx_forecast_restaurant
            ON demand_forecasts(restaurant_id);
    """
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def ensure_peak_hours_table(conn):
    sql = """
        CREATE TABLE IF NOT EXISTS peak_hours (
            id                  SERIAL PRIMARY KEY,
            restaurant_id       VARCHAR(50),
            restaurant_name     VARCHAR(100),
            order_hour          INT,
            order_count         INT,
            is_peak_hour        BOOLEAN,
            created_at          TIMESTAMP DEFAULT NOW()
        );
    """
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


# ─── Load historical order data ───────────────────────────
def load_order_history(conn) -> pd.DataFrame:
    sql = """
        SELECT
            restaurant_id,
            restaurant_name,
            item_id,
            item_name,
            placed_at::date     AS order_date,
            COUNT(*)            AS order_count
        FROM raw_orders
        GROUP BY restaurant_id, restaurant_name,
                 item_id, item_name, placed_at::date
        ORDER BY order_date;
    """
    return pd.read_sql(sql, conn)


def load_hourly_data(conn) -> pd.DataFrame:
    sql = """
        SELECT
            restaurant_id,
            restaurant_name,
            EXTRACT(HOUR FROM placed_at)::int    AS order_hour,
            COUNT(*)                             AS order_count
        FROM raw_orders
        GROUP BY restaurant_id, restaurant_name,
                 EXTRACT(HOUR FROM placed_at)::int
        ORDER BY restaurant_id, order_hour;
    """
    return pd.read_sql(sql, conn)


# ─── Forecasting ──────────────────────────────────────────
def run_forecast_for_item(df_item: pd.DataFrame, item_meta: dict) -> list[dict]:
    """Run Prophet on one restaurant+item combo. Returns list of forecast rows."""
    prophet_df = df_item.rename(columns={"order_date": "ds", "order_count": "y"})
    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])

    model = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
        interval_width=0.80,
    )
    model.fit(prophet_df)

    future   = model.make_future_dataframe(periods=FORECAST_DAYS)
    forecast = model.predict(future)

    # only keep future rows
    last_date  = prophet_df["ds"].max()
    future_fc  = forecast[forecast["ds"] > last_date].copy()

    # mark peak days (top 25% predicted demand)
    threshold  = future_fc["yhat"].quantile(0.75)

    results = []
    for _, row in future_fc.iterrows():
        results.append({
            "restaurant_id":    item_meta["restaurant_id"],
            "restaurant_name":  item_meta["restaurant_name"],
            "item_id":          item_meta["item_id"],
            "item_name":        item_meta["item_name"],
            "forecast_date":    row["ds"].date(),
            "predicted_orders": max(round(row["yhat"], 2), 0),
            "lower_bound":      max(round(row["yhat_lower"], 2), 0),
            "upper_bound":      max(round(row["yhat_upper"], 2), 0),
            "is_peak_day":      bool(row["yhat"] >= threshold),
        })
    return results


def save_forecasts(conn, records: list[dict]):
    # clear today's forecasts before re-inserting
    with conn.cursor() as cur:
        cur.execute("DELETE FROM demand_forecasts WHERE created_at::date = NOW()::date;")

    sql = """
        INSERT INTO demand_forecasts (
            restaurant_id, restaurant_name,
            item_id, item_name,
            forecast_date, predicted_orders,
            lower_bound, upper_bound, is_peak_day
        ) VALUES (
            %(restaurant_id)s, %(restaurant_name)s,
            %(item_id)s, %(item_name)s,
            %(forecast_date)s, %(predicted_orders)s,
            %(lower_bound)s, %(upper_bound)s, %(is_peak_day)s
        );
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_batch(cur, sql, records)
    conn.commit()


# ─── Peak Hour Analysis ───────────────────────────────────
def save_peak_hours(conn, df: pd.DataFrame):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM peak_hours;")

    records = []
    for restaurant_id, grp in df.groupby("restaurant_id"):
        threshold = grp["order_count"].quantile(0.75)
        for _, row in grp.iterrows():
            records.append({
                "restaurant_id":   row["restaurant_id"],
                "restaurant_name": row["restaurant_name"],
                "order_hour":      int(row["order_hour"]),
                "order_count":     int(row["order_count"]),
                "is_peak_hour":    bool(row["order_count"] >= threshold),
            })

    sql = """
        INSERT INTO peak_hours (
            restaurant_id, restaurant_name,
            order_hour, order_count, is_peak_hour
        ) VALUES (
            %(restaurant_id)s, %(restaurant_name)s,
            %(order_hour)s, %(order_count)s, %(is_peak_hour)s
        );
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_batch(cur, sql, records)
    conn.commit()
    print(f"   Peak hours saved for {df['restaurant_id'].nunique()} restaurants.")


# ─── Main ─────────────────────────────────────────────────
def run_forecasting():
    print("🔮 GrubGrid Demand Forecasting starting...")
    print(f"   Forecast horizon : {FORECAST_DAYS} days\n")

    conn = get_conn()
    ensure_forecast_table(conn)
    ensure_peak_hours_table(conn)

    # ── Load data ─────────────────────────────────────────
    print("📥 Loading order history from PostgreSQL...")
    df_orders  = load_order_history(conn)
    df_hourly  = load_hourly_data(conn)
    print(f"   {len(df_orders)} daily order records loaded.")
    print(f"   {df_orders['item_id'].nunique()} unique items across "
          f"{df_orders['restaurant_id'].nunique()} restaurants.\n")

    # ── Peak hours ────────────────────────────────────────
    print("⏰ Calculating peak hours...")
    save_peak_hours(conn, df_hourly)

    # ── Forecast per item ─────────────────────────────────
    all_forecasts = []
    groups = df_orders.groupby(["restaurant_id", "item_id"])
    total  = len(groups)

    print(f"\n📈 Running Prophet forecasts for {total} item combos...\n")

    for idx, ((restaurant_id, item_id), grp) in enumerate(groups, 1):
        item_meta = {
            "restaurant_id":   restaurant_id,
            "restaurant_name": grp["restaurant_name"].iloc[0],
            "item_id":         item_id,
            "item_name":       grp["item_name"].iloc[0],
        }

        if len(grp) < MIN_ROWS_FOR_FORECAST:
            print(f"   ⏭️  [{idx}/{total}] Skipping {item_meta['item_name']} "
                  f"@ {item_meta['restaurant_name']} — insufficient history "
                  f"({len(grp)} rows)")
            continue

        try:
            forecasts = run_forecast_for_item(grp, item_meta)
            all_forecasts.extend(forecasts)
            peak_days = sum(1 for f in forecasts if f["is_peak_day"])
            print(f"   ✅ [{idx}/{total}] {item_meta['item_name']} "
                  f"@ {item_meta['restaurant_name']} — "
                  f"{len(forecasts)} days forecast, {peak_days} peak days")
        except Exception as e:
            print(f"   ❌ [{idx}/{total}] Failed for {item_meta['item_name']}: {e}")

    # ── Save ──────────────────────────────────────────────
    if all_forecasts:
        print(f"\n💾 Saving {len(all_forecasts)} forecast records...")
        save_forecasts(conn, all_forecasts)
        print("   Forecasts saved ✅")
    else:
        print("\n⚠️  No forecasts generated — run the producer longer to build history.")

    conn.close()
    print("\n🎉 Forecasting complete!")


if __name__ == "__main__":
    run_forecasting()