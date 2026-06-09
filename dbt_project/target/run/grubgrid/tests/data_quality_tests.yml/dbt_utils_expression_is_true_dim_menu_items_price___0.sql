
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  



select
    1
from "grubgrid"."dbt_grubgrid_marts"."dim_menu_items"

where not(price > 0)


  
  
      
    ) dbt_internal_test