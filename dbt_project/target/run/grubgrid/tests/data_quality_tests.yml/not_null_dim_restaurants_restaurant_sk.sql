
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select restaurant_sk
from "grubgrid"."dbt_grubgrid_marts"."dim_restaurants"
where restaurant_sk is null



  
  
      
    ) dbt_internal_test