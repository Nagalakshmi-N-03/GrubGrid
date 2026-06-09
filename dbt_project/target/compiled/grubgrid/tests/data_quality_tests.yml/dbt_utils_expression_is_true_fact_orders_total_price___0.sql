



select
    1
from "grubgrid"."dbt_grubgrid_marts"."fact_orders"

where not(total_price >= 0)

