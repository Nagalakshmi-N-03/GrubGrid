



select
    1
from "grubgrid"."dbt_grubgrid_staging"."stg_orders"

where not(quantity > 0)

