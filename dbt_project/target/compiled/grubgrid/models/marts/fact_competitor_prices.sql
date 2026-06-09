-- fact_competitor_prices.sql
-- Fact table for daily competitor price snapshots

with prices as (
    select * from "grubgrid"."dbt_grubgrid_staging"."stg_competitor_prices"
),

restaurants as (
    select restaurant_name, restaurant_sk from "grubgrid"."dbt_grubgrid_marts"."dim_restaurants"
),

final as (
    select
        p.price_record_id,
        r.restaurant_sk,
        p.scrape_date                               as date_id,

        -- dimensions
        p.competitor_name,
        p.restaurant_name,
        p.item_name,

        -- measures
        p.our_price,
        p.competitor_price,
        p.price_gap,
        p.abs_price_gap,
        p.price_gap_pct,

        -- flags
        p.is_undercut,
        p.alert_severity,

        -- timestamps
        p.scraped_at,
        current_timestamp                           as dbt_updated_at

    from prices p
    left join restaurants r using (restaurant_name)
)

select * from final