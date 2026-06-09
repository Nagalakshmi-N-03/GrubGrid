
    
    

select
    price_record_id as unique_field,
    count(*) as n_records

from "grubgrid"."dbt_grubgrid_staging"."stg_competitor_prices"
where price_record_id is not null
group by price_record_id
having count(*) > 1


