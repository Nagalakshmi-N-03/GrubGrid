-- dim_locations.sql
-- Delivery location dimension derived from orders

with locations as (
    select distinct
        trim(location)  as location_name
    from {{ ref('stg_orders') }}
    where location is not null
)

select
    {{ dbt_utils.generate_surrogate_key(['location_name']) }}   as location_sk,
    location_name,
    -- In a real project these would come from a geocoding API
    'Chennai'                                                   as city,
    'Tamil Nadu'                                                as state,
    'India'                                                     as country,
    current_timestamp                                           as dbt_updated_at
from locations