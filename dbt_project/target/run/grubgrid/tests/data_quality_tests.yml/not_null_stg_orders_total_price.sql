
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select total_price
from "grubgrid"."dbt_grubgrid_staging"."stg_orders"
where total_price is null



  
  
      
    ) dbt_internal_test