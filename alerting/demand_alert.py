"""
demand_alert.py
Checks demand_forecasts table for upcoming spike days
and prints alerts (or emails if SMTP is configured).
"""

import os
import smtplib
import psycopg2
import pandas as pd
from datetime import date, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("POSTGRES_HOST", "localhost"),
    "port":     int(os.getenv("POSTGRES_PORT", 5432)),
    "dbname":   os.getenv("POSTGRES_DB", "grubgrid"),
    "user":     os.getenv("POSTGRES_USER", "grubgrid_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "grubgrid_pass"),
}

SMTP_HOST     = os.getenv("SMTP_HOST", "")
SMTP_PORT     = int(os.getenv("SMTP_PORT", 587))
SMTP_USER     = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ALERT_EMAIL   = os.getenv("ALERT_EMAIL", "")

SPIKE_THRESHOLD_PCT = 50   # flag if predicted > 1.5x average
LOOKAHEAD_DAYS      = 7    # look 7 days ahead


def load_forecasts(conn) -> pd.DataFrame:
    today = date.today()
    cutoff = today + timedelta(days=LOOKAHEAD_DAYS)
    df = pd.read_sql("""
        SELECT
            restaurant_name,
            item_name,
            forecast_date,
            predicted_orders,
            lower_bound,
            upper_bound
        FROM demand_forecasts
        WHERE forecast_date BETWEEN %(today)s AND %(cutoff)s
        ORDER BY restaurant_name, item_name, forecast_date
    """, conn, params={"today": today, "cutoff": cutoff})
    return df


def detect_spikes(df: pd.DataFrame) -> pd.DataFrame:
    avg = (
        df.groupby(["restaurant_name", "item_name"])["predicted_orders"]
        .mean()
        .reset_index()
        .rename(columns={"predicted_orders": "avg_predicted"})
    )
    df = df.merge(avg, on=["restaurant_name", "item_name"])
    df["spike_pct"] = ((df["predicted_orders"] - df["avg_predicted"]) / df["avg_predicted"] * 100).round(1)
    spikes = df[df["spike_pct"] >= SPIKE_THRESHOLD_PCT].copy()
    return spikes.sort_values("spike_pct", ascending=False)


def format_alert_text(spikes: pd.DataFrame) -> str:
    lines = [
        "=" * 60,
        "  🚨 GrubGrid Demand Spike Alert",
        f"  Period: next {LOOKAHEAD_DAYS} days",
        "=" * 60,
        "",
    ]
    for _, row in spikes.iterrows():
        lines.append(
            f"  🔺 {row['restaurant_name']} | {row['item_name']}"
            f"\n     Date: {row['forecast_date']}"
            f"\n     Predicted: {row['predicted_orders']:.0f} orders"
            f"\n     Spike:     +{row['spike_pct']:.1f}% above average"
        )
        lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def send_email(subject: str, body: str):
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL]):
        print("  ⚠️  SMTP not configured — skipping email.")
        return
    msg = MIMEMultipart()
    msg["From"]    = SMTP_USER
    msg["To"]      = ALERT_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
    print(f"  📧 Alert email sent to {ALERT_EMAIL}")


def run_demand_alert():
    print("🚨 GrubGrid Demand Alert starting...")
    conn = psycopg2.connect(**DB_CONFIG)

    print(f"  Loading forecasts for next {LOOKAHEAD_DAYS} days...")
    df = load_forecasts(conn)

    if df.empty:
        print("  No forecast data found. Run demand_forecast.py first.")
        conn.close()
        return

    print(f"  {len(df)} forecast rows loaded.")
    spikes = detect_spikes(df)

    if spikes.empty:
        print(f"  ✅ No demand spikes detected (threshold: +{SPIKE_THRESHOLD_PCT}%).")
    else:
        print(f"  🔺 {len(spikes)} spike events detected!\n")
        alert_text = format_alert_text(spikes)
        print(alert_text)
        send_email(
            subject=f"GrubGrid: {len(spikes)} Demand Spikes Detected",
            body=alert_text,
        )

    conn.close()
    print("\n✅ Demand alert check complete.")


if __name__ == "__main__":
    run_demand_alert()