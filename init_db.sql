-- ─── GrubGrid PostgreSQL Init Script ───────────────────────────────────────
-- Runs automatically on first docker-compose up via docker-entrypoint-initdb.d

-- ─── Raw Orders Table (populated by Kafka consumer) ─────────────────────────
CREATE TABLE IF NOT EXISTS raw_orders (
    order_id        VARCHAR(50) PRIMARY KEY,
    restaurant_id   VARCHAR(50),
    restaurant_name VARCHAR(100),
    item_id         VARCHAR(50),
    item_name       VARCHAR(100),
    quantity        INT,
    unit_price      NUMERIC(10, 2),
    total_price     NUMERIC(10, 2),
    customer_id     VARCHAR(50),
    location        VARCHAR(100),
    status          VARCHAR(30),    -- placed | preparing | out_for_delivery | delivered
    placed_at       TIMESTAMP DEFAULT NOW(),
    delivered_at    TIMESTAMP
);

-- ─── Competitor Prices Table (populated by scraper) ──────────────────────────
CREATE TABLE IF NOT EXISTS competitor_prices (
    id                  SERIAL PRIMARY KEY,
    scraped_at          TIMESTAMP DEFAULT NOW(),
    competitor_name     VARCHAR(100),
    restaurant_name     VARCHAR(100),
    item_name           VARCHAR(100),
    competitor_price    NUMERIC(10, 2),
    our_price           NUMERIC(10, 2),
    price_gap           NUMERIC(10, 2),   -- our_price - competitor_price
    is_undercut         BOOLEAN           -- TRUE if competitor is cheaper
);

-- ─── Menu Items Table (platform's own prices) ────────────────────────────────
CREATE TABLE IF NOT EXISTS menu_items (
    item_id         VARCHAR(50) PRIMARY KEY,
    restaurant_id   VARCHAR(50),
    item_name       VARCHAR(100),
    category        VARCHAR(50),
    price           NUMERIC(10, 2),
    is_available    BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ─── Restaurants Table ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS restaurants (
    restaurant_id   VARCHAR(50) PRIMARY KEY,
    restaurant_name VARCHAR(100),
    cuisine_type    VARCHAR(50),
    location        VARCHAR(100),
    rating          NUMERIC(3, 1),
    is_active       BOOLEAN DEFAULT TRUE,
    joined_at       TIMESTAMP DEFAULT NOW()
);

-- ─── Indexes for query performance ───────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_raw_orders_placed_at     ON raw_orders(placed_at);
CREATE INDEX IF NOT EXISTS idx_raw_orders_restaurant    ON raw_orders(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_raw_orders_status        ON raw_orders(status);
CREATE INDEX IF NOT EXISTS idx_competitor_scraped_at    ON competitor_prices(scraped_at);
CREATE INDEX IF NOT EXISTS idx_competitor_is_undercut   ON competitor_prices(is_undercut);