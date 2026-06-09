



select
    1
from "grubgrid"."dbt_grubgrid_marts"."dim_menu_items"

where not(price > 0)

