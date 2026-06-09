



select
    1
from "grubgrid"."dbt_grubgrid_staging"."stg_competitor_prices"

where not(competitor_price > 0)

