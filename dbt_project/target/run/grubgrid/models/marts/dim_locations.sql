
  
    

  create  table "grubgrid"."dbt_grubgrid_marts"."dim_locations__dbt_tmp"
  
  
    as
  
  (
    -- dim_locations.sql
-- Delivery location dimension derived from orders

with locations as (
    select distinct
        trim(location)  as location_name
    from "grubgrid"."dbt_grubgrid_staging"."stg_orders"
    where location is not null
)

select
    md5(cast(coalesce(cast(location_name as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT))   as location_sk,
    location_name,
    -- In a real project these would come from a geocoding API
    'Chennai'                                                   as city,
    'Tamil Nadu'                                                as state,
    'India'                                                     as country,
    current_timestamp                                           as dbt_updated_at
from locations
  );
  