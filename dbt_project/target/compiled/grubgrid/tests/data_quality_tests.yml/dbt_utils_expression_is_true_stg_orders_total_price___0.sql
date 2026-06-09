



select
    1
from "grubgrid"."dbt_grubgrid_staging"."stg_orders"

where not(total_price >= 0)

