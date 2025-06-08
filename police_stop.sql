CREATE TABLE police_stops (
    stop_date DATE,
    stop_time TIME,
    country_name VARCHAR(50),
    driver_gender CHAR(1),
    driver_age_raw INT,
    driver_age INT,
    driver_race VARCHAR(50),
    violation_raw VARCHAR(100),
    violation VARCHAR(100),
    search_conducted BOOLEAN,
    search_type VARCHAR(100),
    stop_outcome VARCHAR(50),
    is_arrested BOOLEAN,
    stop_duration VARCHAR(20),
    drugs_related_stop BOOLEAN,
    vehicle_number VARCHAR(20)
);

copy police_stops from 'D:\MDTE21\Police\traffic_stops_cleaned.csv' delimiter ',' csv header

select * from police_stops

--(Medium level):

--1.What are the top 10 vehicle_Number involved in drug-related stops?
select vehicle_number, count(*) as stop_count from police_stops where drugs_related_stop = True group by vehicle_number order by stop_count desc limit 10;


--2.	Which vehicles were most frequently searched?
select vehicle_number, count(*) as stop_count from police_stops where search_conducted = True group by vehicle_number order by stop_count desc limit 10;


--4.	Which driver age group had the highest arrest rate?
select driver_age, count(*) as total_stop, sum(case when is_arrested = True then 1 else 0 end) as total_arrests, round(100.0 * sum(case when is_arrested = True then 1 else 0 end)/count(*),2) as arrested_rate
from police_stops where driver_age is not null group by driver_age order by arrested_rate desc limit 5;


--5.	What is the gender distribution of drivers stopped in each country?
select country_name, driver_gender, count(*) as total_stop 
from police_stops where country_name is not null and  driver_gender is not null 
group by country_name, driver_gender order by country_name, driver_gender;


--6.	Which race and gender combination has the highest search rate?
select driver_gender,driver_race, count(*) as total_stops, sum(case when search_conducted = True then 1 else 0 end) as total_search_conducted, round(100.0 * sum(case when search_conducted = True then 1 else 0 end)/count(*),2) as search_conducted_rate
from police_stops where driver_gender is not null and driver_race is not null group by driver_gender,driver_race order by driver_gender,driver_race desc limit 1;


--7.	What time of day sees the most traffic stops?
select extract(hour from stop_time) as stop_hour, count(*) as total_stop 
from police_stops where stop_time is not null group by stop_hour order by total_stop desc limit 1;


--8.	What is the average stop duration for different violations?
select violation, round (avg(case stop_duration when '0-15 Min' then 8 when '16-30 Min' then 23 when '30-45 Min' then 40 end), 2) as average_duration
from police_stops where violation is not null group by violation order by average_duration desc;



--9.	Are stops during the night more likely to lead to arrests?
SELECT case when extract (hours from stop_time) between 6 and 19 then 'day' else 'night' end as day_night, count(*) as total_stop, sum(case when is_arrested = True then 1 else 0 end) as total_arrested,
round(100.0*sum(case when is_arrested = True then 1 else 0 end)/count(*), 2) as arrested_rate
from police_stops where stop_time is not null group by day_night order by day_night;


--10.	Which violations are most associated with searches or arrests?
select violation, count(*) filter(where search_conducted = True) as total_search, count(*) filter (where is_arrested = True) as total_arrested
from police_stops group by violation order by total_search desc, total_arrested desc;


--11.	Which violations are most common among younger drivers (<25)?
select violation, count(*) as total_violation_count from police_stops where driver_age < 25 group by violation order by total_violation_count desc;


--12.	Is there a violation that rarely results in search or arrest?
select violation, count(*) as total_violation_count, sum(case when search_conducted = True then 1 else 0 end) as search, sum(case when is_arrested = True then 1 else 0 end) as arrest,
round(100.0 * sum(case when search_conducted = True then 1 else 0 end)/count(*),2) as total_search_rate, round(100.0 * sum(case when is_arrested = True then 1 else 0 end)/count(*),2)as total_arrest_rate
from police_stops group by violation order by total_search_rate desc, total_arrest_rate desc;


--13.	Which countries report the highest rate of drug-related stops?
select country_name, count(*) as total_stop, sum(case when drugs_related_stop = True then 1 else 0 end)as total_drugs_related_stops, round(100.0*(sum(case when drugs_related_stop = True then 1 else 0 end))/count(*),2) as drugs_related_stop_rate
from police_stops group by country_name order by drugs_related_stop_rate desc;

--14.	What is the arrest rate by country and violation?
select country_name, violation, count(*) as total_stop, sum(case when is_arrested = True then 1 else 0 end)as arrest, round(100.0 * sum(case when is_arrested = True then 1 else 0 end)/ count(*),2) as arrested_rate
from police_stops group by country_name, violation order by arrested_rate desc;

--15.	Which country has the most stops with search conducted?
select country_name, count(*) as total_seach_conducted from police_stops where search_conducted = True group by country_name order by total_seach_conducted desc limit 1;

--(Complex): 

--1.Yearly Breakdown of Stops and Arrests by Country (Using Subquery and Window Functions)
select year,country_name,total_stops,total_arrests,
round(100.0 * total_arrests/total_stops,2)as arreste_rate,
sum(total_arrests) over (partition by country_name order by year rows between UNBOUNDED PRECEDING and current row) as cumulative_arrests
from( select extract(year from stop_date) as year, country_name, count(*) as total_stops, sum(case when is_arrested = true then 1 else 0 end) as total_arrests
from police_stops group by year, country_name) as yearly_data order by country_name, year;

--2.Driver Violation Trends Based on Age and Race (Join with Subquery)
-- Subquery: Categorize drivers into age groups
WITH age_grouped AS (
  SELECT *,
    CASE 
      WHEN driver_age < 18 THEN 'Under 18'
      WHEN driver_age BETWEEN 18 AND 24 THEN '18-24'
      WHEN driver_age BETWEEN 25 AND 34 THEN '25-34'
      WHEN driver_age BETWEEN 35 AND 44 THEN '35-44'
      WHEN driver_age BETWEEN 45 AND 54 THEN '45-54'
      WHEN driver_age BETWEEN 55 AND 64 THEN '55-64'
      ELSE '65+'
    END AS age_group
  FROM police_stops
)

-- Main query: Count violations by age group and race
SELECT 
  age_group,
  driver_race,
  violation,
  COUNT(*) AS violation_count
FROM age_grouped
GROUP BY age_group, driver_race, violation
ORDER BY age_group, driver_race, violation_count DESC;

--3.Time Period Analysis of Stops (Joining with Date Functions) , Number of Stops by Year,Month, Hour of the Day

Select extract (year from stop_date) as year,
extract(month from stop_date) as month,
extract (hour from stop_time) as hour,
count(*) as total_stops
from police_stops
where stop_date is not null and stop_time is not null
group by year, month, hour
order by year, month, hour;

--4.Violations with High Search and Arrest Rates (Window Function)
select violation, count(*) as total_stops,
sum(case when search_conducted = True then 1 else 0 end) as total_search,
sum(case when is_arrested = True then 1 else 0 end) as total_arrested,
round(100.0 * sum(case when search_conducted = True then 1 else 0 end)/count(*) over(partition by violation),2) as search_rate,
round(100.0 * sum(case when is_arrested = True then 1 else 0 end)/count(*) over(partition by violation),2) as arrested_rate
from police_stops
group by violation
order by search_rate, arrested_rate;

--5.Driver Demographics by Country (Age, Gender, and Race)
select country_name, driver_age,driver_race,
round(avg(driver_age),1) as avg_age,
count(*) as total_drivers
from police_stops
where country_name is not null
and driver_age is not null
and driver_gender is not null
and driver_race is not null

group by country_name, driver_age,driver_race
order by country_name, driver_age,driver_race;

--6.Top 5 Violations with Highest Arrest Rates

select violation, count(*) as total_stops,
sum(case when is_arrested = True then 1 else 0 end) as total_arrests,
round(100.0 * sum(case when is_arrested = True then 1 else 0 end)/count(*),2)as arrest_rate
from police_stops
where violation is not null
group by violation
order by arrest_rate desc limit 5;