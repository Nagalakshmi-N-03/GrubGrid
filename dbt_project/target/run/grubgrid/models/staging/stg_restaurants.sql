
  create view "grubgrid"."dbt_grubgrid_staging"."stg_restaurants__dbt_tmp"
    
    
  as (
    -- stg_restaurants.sql
-- Cleans restaurant master data
-- Falls back to deriving unique restaurants from raw_orders
-- if the restaurants table is empty

with from_table as (
    select
        restaurant_id,
        trim(restaurant_name)   as restaurant_name,
        trim(cuisine_type)      as cuisine_type,
        trim(location)          as location,
        rating::numeric(3,1)    as rating,
        is_active,
        joined_at::timestamp    as joined_at
    from "grubgrid"."public"."restaurants"
),

from_orders as (
    select distinct
        restaurant_id,
        restaurant_name,
        null::varchar           as cuisine_type,
        null::varchar           as location,
        null::numeric(3,1)      as rating,
        true                    as is_active,
        min(placed_at)          as joined_at
    from "grubgrid"."public"."raw_orders"
    group by restaurant_id, restaurant_name
),

combined as (
    select * from from_table
    union all
    select * from from_orders
    where restaurant_id not in (select restaurant_id from from_table)
)

select * from combined
  );