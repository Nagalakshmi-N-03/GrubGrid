-- dim_menu_items.sql
-- Menu item dimension table

with stg as (
    select * from {{ ref('stg_menu_items') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['item_id']) }}         as item_sk,
    item_id,
    restaurant_id,
    item_name,
    coalesce(category, 'Uncategorised')                         as category,
    price,
    is_available,
    created_at,
    current_timestamp                                           as dbt_updated_at
from stg