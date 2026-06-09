
  
    

  create  table "grubgrid"."dbt_grubgrid_marts"."fact_orders__dbt_tmp"
  
  
    as
  
  (
    -- fact_orders.sql
-- Central fact table — one row per order

with orders as (
    select * from "grubgrid"."dbt_grubgrid_staging"."stg_orders"
),

restaurants as (
    select restaurant_id, restaurant_sk from "grubgrid"."dbt_grubgrid_marts"."dim_restaurants"
),

items as (
    select item_id, item_sk from "grubgrid"."dbt_grubgrid_marts"."dim_menu_items"
),

locations as (
    select location_name, location_sk from "grubgrid"."dbt_grubgrid_marts"."dim_locations"
),

final as (
    select
        -- keys
        o.order_id,
        r.restaurant_sk,
        i.item_sk,
        l.location_sk,
        o.order_date                                as date_id,

        -- degenerate dimensions
        o.order_id                                  as order_natural_key,
        o.customer_id,
        o.status,

        -- measures
        o.quantity,
        o.unit_price,
        o.total_price,
        o.delivery_minutes,

        -- time attributes
        o.placed_at,
        o.delivered_at,
        o.order_hour,
        o.day_of_week,

        current_timestamp                           as dbt_updated_at

    from orders o
    left join restaurants r using (restaurant_id)
    left join items       i using (item_id)
    left join locations   l on l.location_name = o.location
)

select * from final
  );
  