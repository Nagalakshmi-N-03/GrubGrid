
    
    

with all_values as (

    select
        status as value_field,
        count(*) as n_records

    from "grubgrid"."dbt_grubgrid_staging"."stg_orders"
    group by status

)

select *
from all_values
where value_field not in (
    'placed','preparing','out_for_delivery','delivered'
)


