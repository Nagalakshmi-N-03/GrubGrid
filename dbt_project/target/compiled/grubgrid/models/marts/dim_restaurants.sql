-- dim_restaurants.sql
-- Restaurant dimension table

with stg as (
    select * from "grubgrid"."dbt_grubgrid_staging"."stg_restaurants"
)

select
    md5(cast(coalesce(cast(restaurant_id as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT))    as restaurant_sk,
    restaurant_id,
    restaurant_name,
    coalesce(cuisine_type, 'Unknown')                           as cuisine_type,
    coalesce(location, 'Unknown')                               as location,
    coalesce(rating, 0.0)                                       as rating,
    is_active,
    joined_at,
    current_timestamp                                           as dbt_updated_at
from stg