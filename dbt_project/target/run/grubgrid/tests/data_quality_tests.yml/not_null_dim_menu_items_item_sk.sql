
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select item_sk
from "grubgrid"."dbt_grubgrid_marts"."dim_menu_items"
where item_sk is null



  
  
      
    ) dbt_internal_test