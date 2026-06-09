
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    restaurant_sk as unique_field,
    count(*) as n_records

from "grubgrid"."dbt_grubgrid_marts"."dim_restaurants"
where restaurant_sk is not null
group by restaurant_sk
having count(*) > 1



  
  
      
    ) dbt_internal_test