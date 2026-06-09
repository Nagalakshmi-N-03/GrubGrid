
  
    

  create  table "grubgrid"."dbt_grubgrid_marts"."dim_menu_items__dbt_tmp"
  
  
    as
  
  (
    -- dim_menu_items.sql
-- Menu item dimension table

with stg as (
    select * from "grubgrid"."dbt_grubgrid_staging"."stg_menu_items"
)

select
    md5(cast(coalesce(cast(item_id as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT))         as item_sk,
    item_id,
    restaurant_id,
    item_name,
    coalesce(category, 'Uncategorised')                         as category,
    price,
    is_available,
    created_at,
    current_timestamp                                           as dbt_updated_at
from stg
  );
  