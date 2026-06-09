-- stg_menu_items.sql
-- Cleans menu item master data
-- Falls back to deriving items from raw_orders if menu_items table is empty

with from_table as (
    select
        item_id,
        restaurant_id,
        trim(item_name)         as item_name,
        trim(category)          as category,
        price::numeric(10,2)    as price,
        is_available,
        created_at::timestamp   as created_at
    from {{ source('grubgrid_raw', 'menu_items') }}
),

from_orders as (
    select distinct
        item_id,
        restaurant_id,
        item_name,
        null::varchar           as category,
        unit_price              as price,
        true                    as is_available,
        min(placed_at)          as created_at
    from {{ source('grubgrid_raw', 'raw_orders') }}
    group by item_id, restaurant_id, item_name, unit_price
),

combined as (
    select * from from_table
    union all
    select * from from_orders
    where item_id not in (select item_id from from_table)
)

select * from combined