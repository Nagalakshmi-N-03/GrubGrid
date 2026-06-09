-- dim_dates.sql
-- Date dimension generated from order date range

with date_spine as (
    





with rawdata as (

    

    

    with p as (
        select 0 as generated_number union all select 1
    ), unioned as (

    select

    
    p0.generated_number * power(2, 0)
     + 
    
    p1.generated_number * power(2, 1)
     + 
    
    p2.generated_number * power(2, 2)
     + 
    
    p3.generated_number * power(2, 3)
     + 
    
    p4.generated_number * power(2, 4)
     + 
    
    p5.generated_number * power(2, 5)
     + 
    
    p6.generated_number * power(2, 6)
     + 
    
    p7.generated_number * power(2, 7)
     + 
    
    p8.generated_number * power(2, 8)
     + 
    
    p9.generated_number * power(2, 9)
     + 
    
    p10.generated_number * power(2, 10)
    
    
    + 1
    as generated_number

    from

    
    p as p0
     cross join 
    
    p as p1
     cross join 
    
    p as p2
     cross join 
    
    p as p3
     cross join 
    
    p as p4
     cross join 
    
    p as p5
     cross join 
    
    p as p6
     cross join 
    
    p as p7
     cross join 
    
    p as p8
     cross join 
    
    p as p9
     cross join 
    
    p as p10
    
    

    )

    select *
    from unioned
    where generated_number <= 1095
    order by generated_number



),

all_periods as (

    select (
        

    cast('2024-01-01' as date) + ((interval '1 day') * (row_number() over (order by 1) - 1))


    ) as date_day
    from rawdata

),

filtered as (

    select *
    from all_periods
    where date_day <= cast('2026-12-31' as date)

)

select * from filtered


),

final as (
    select
        cast(date_day as date)                              as date_id,
        extract(year  from date_day)::integer               as year,
        extract(month from date_day)::integer               as month,
        extract(day   from date_day)::integer               as day,
        extract(dow   from date_day)::integer               as day_of_week,   -- 0=Sun
        extract(week  from date_day)::integer               as week_of_year,
        extract(quarter from date_day)::integer             as quarter,

        to_char(date_day, 'Month')                          as month_name,
        to_char(date_day, 'Day')                            as day_name,

        case extract(dow from date_day)::integer
            when 0 then true
            when 6 then true
            else false
        end                                                 as is_weekend,

        case extract(month from date_day)::integer
            when 1  then 'Q1' when 2  then 'Q1' when 3  then 'Q1'
            when 4  then 'Q2' when 5  then 'Q2' when 6  then 'Q2'
            when 7  then 'Q3' when 8  then 'Q3' when 9  then 'Q3'
            when 10 then 'Q4' when 11 then 'Q4' when 12 then 'Q4'
        end                                                 as fiscal_quarter

    from date_spine
)

select * from final