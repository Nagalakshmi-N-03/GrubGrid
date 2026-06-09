
    
    

select
    item_sk as unique_field,
    count(*) as n_records

from "grubgrid"."dbt_grubgrid_marts"."dim_menu_items"
where item_sk is not null
group by item_sk
having count(*) > 1


