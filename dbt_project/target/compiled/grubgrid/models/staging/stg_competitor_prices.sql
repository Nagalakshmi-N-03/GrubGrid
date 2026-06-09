-- stg_competitor_prices.sql
-- Cleans competitor price scrape data

with source as (
    select * from "grubgrid"."public"."competitor_prices"
),

cleaned as (
    select
        id                                          as price_record_id,
        scraped_at::timestamp                       as scraped_at,
        scraped_at::date                            as scrape_date,
        trim(competitor_name)                       as competitor_name,
        trim(restaurant_name)                       as restaurant_name,
        trim(item_name)                             as item_name,
        competitor_price::numeric(10,2)             as competitor_price,
        our_price::numeric(10,2)                    as our_price,
        price_gap::numeric(10,2)                    as price_gap,
        is_undercut,

        -- derived
        abs(price_gap)                              as abs_price_gap,
        round(
            (abs(price_gap) / nullif(our_price, 0)) * 100, 2
        )                                           as price_gap_pct,

        case
            when abs(price_gap) >= 30 then 'critical'
            when abs(price_gap) >= 15 then 'high'
            when abs(price_gap) >= 10 then 'medium'
            else 'low'
        end                                         as alert_severity

    from source
    where our_price > 0
      and competitor_price > 0
)

select * from cleaned