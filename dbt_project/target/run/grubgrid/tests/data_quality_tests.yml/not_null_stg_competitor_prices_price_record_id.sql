
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select price_record_id
from "grubgrid"."dbt_grubgrid_staging"."stg_competitor_prices"
where price_record_id is null



  
  
      
    ) dbt_internal_test