"""
migrate_to_neon.py
Copies all data from local PostgreSQL to Neon cloud database.
Run once to migrate existing data.
"""

import psycopg2
import psycopg2.extras

LOCAL_CONN_STR = "host=localhost port=5432 dbname=grubgrid user=grubgrid_user password=grubgrid_pass"
NEON_CONN_STR  = "postgresql://neondb_owner:npg_2JvT7gUCOMSy@ep-rapid-darkness-ao16vhgr-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

TABLES = ["restaurants", "menu_items", "raw_orders", "competitor_prices", "demand_forecasts", "peak_hours"]


def migrate_table(local_cur, neon_cur, neon_conn, table: str):
    print(f"  Migrating {table}...")
    local_cur.execute(f"SELECT * FROM {table};")
    rows = local_cur.fetchall()

    if not rows:
        print(f"    ⚠️  {table} is empty — skipping.")
        return

    # get column names
    col_names = [desc[0] for desc in local_cur.description]
    cols      = ", ".join(col_names)
    placeholders = ", ".join(["%s"] * len(col_names))

    sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders}) ON CONFLICT DO NOTHING;"

    psycopg2.extras.execute_batch(neon_cur, sql, rows)
    neon_conn.commit()
    print(f"    ✅ {len(rows)} rows migrated.")


def run_migration():
    print("🚀 GrubGrid — Migrating local data to Neon...\n")

    local_conn = psycopg2.connect(LOCAL_CONN_STR)
    neon_conn  = psycopg2.connect(NEON_CONN_STR)

    local_cur = local_conn.cursor()
    neon_cur  = neon_conn.cursor()

    # create extra tables on neon if they don't exist
    neon_cur.execute("""
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
        CREATE TABLE IF NOT EXISTS peak_hours (
            id                  SERIAL PRIMARY KEY,
            restaurant_id       VARCHAR(50),
            restaurant_name     VARCHAR(100),
            order_hour          INT,
            order_count         INT,
            is_peak_hour        BOOLEAN,
            created_at          TIMESTAMP DEFAULT NOW()
        );
    """)
    neon_conn.commit()

    for table in TABLES:
        try:
            migrate_table(local_cur, neon_cur, neon_conn, table)
        except Exception as e:
            print(f"    ❌ Failed to migrate {table}: {e}")
            neon_conn.rollback()

    local_conn.close()
    neon_conn.close()
    print("\n✅ Migration complete!")


if __name__ == "__main__":
    run_migration()