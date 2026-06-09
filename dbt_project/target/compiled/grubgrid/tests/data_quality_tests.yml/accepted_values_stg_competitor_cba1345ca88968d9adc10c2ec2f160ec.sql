
    
    

with all_values as (

    select
        alert_severity as value_field,
        count(*) as n_records

    from "grubgrid"."dbt_grubgrid_staging"."stg_competitor_prices"
    group by alert_severity

)

select *
from all_values
where value_field not in (
    'low','medium','high','critical'
)


