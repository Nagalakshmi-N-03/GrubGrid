-- dim_dates.sql
-- Date dimension generated from order date range

with date_spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2024-01-01' as date)",
        end_date="cast('2026-12-31' as date)"
    ) }}
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