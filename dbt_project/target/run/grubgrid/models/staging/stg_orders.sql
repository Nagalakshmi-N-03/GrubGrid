
  create view "grubgrid"."dbt_grubgrid_staging"."stg_orders__dbt_tmp"
    
    
  as (
    -- stg_orders.sql
-- Cleans and standardises raw orders from PostgreSQL

with source as (
    select * from "grubgrid"."public"."raw_orders"
),

cleaned as (
    select
        order_id,
        restaurant_id,
        trim(restaurant_name)                       as restaurant_name,
        item_id,
        trim(item_name)                             as item_name,
        quantity::integer                           as quantity,
        unit_price::numeric(10,2)                   as unit_price,
        total_price::numeric(10,2)                  as total_price,
        customer_id,
        trim(location)                              as location,
        lower(trim(status))                         as status,
        placed_at::timestamp                        as placed_at,
        delivered_at::timestamp                     as delivered_at,

        -- derived columns
        date_trunc('hour', placed_at)               as placed_hour,
        placed_at::date                             as order_date,
        extract(hour from placed_at)::integer       as order_hour,
        extract(dow  from placed_at)::integer       as day_of_week,  -- 0=Sun, 6=Sat

        case
            when status = 'delivered' and delivered_at is not null
            then extract(epoch from (delivered_at - placed_at)) / 60
        end                                         as delivery_minutes

    from source
    where order_id is not null
      and total_price > 0
)

select * from cleaned
  );