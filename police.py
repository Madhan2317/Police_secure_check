import pandas as pd 
import streamlit as st
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

#Dataset Path
df = pd.read_csv('D:\\MDTE21\\Police\\traffic_stops - traffic_stops_with_vehicle_number.csv')


#total number of null values in the dataset
total_null = df.isnull().sum()

#drop any Nan values
df = df.dropna()

#save the cleaned dataset
df.to_csv('traffic_stops_cleaned.csv', index=False)

#database connection
connection = psycopg2.connect(
    host="localhost",
    user="postgres",
    password="Madhan2317",
    port = 5432,
    database = "Policestop" # Ensure this database exists or create it before running the code
)

connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)  # This is to set the isolation level to autocommit mode

transulator = connection.cursor()


# Streamlit UI
st.set_page_config(layout="wide")

st.title("Police Check post log 🚓")

st.write("This form is used to record and monitor vehicle stops conducted at police check posts. Officers or authorized personnel are requested to log accurate information about each stop, including the date, time, location, driver details, and nature of the stop.")

# Create a form for police log entry
st.title("police_log_form 📝")
with st.form("police_log_form 📝"):
    stop_date = st.date_input("Stop Date 📅")
    stop_time = st.time_input("Stop Time 🕒")
    country_name = st.text_input("Country Name 🌐")
    driver_gender = st.selectbox("Driver Gender", ["Male 👨", "Female 👩", "Other 	🧑‍🦱 or ⚧️"])
    driver_age = st.number_input("Driver Age", min_value=16, max_value=100, step=1)
    driver_race = st.text_input("🧑🏾‍🤝‍🧑🏻Driver Race")
    search_conducted = st.selectbox("🔍 Was a Search Conducted? 🕵️‍♂️", [0, 1])
    search_type = st.text_input("🚗Search Type🔍")
    drugs_related = st.selectbox("Was it Drug Related? 💊", [0, 1])
    stop_duration = st.selectbox("Stop Duration ⏱", ["0-15 Min", "16-30 Min", "30+ Min"])
    vehicle_number = st.text_input("🚗Vehicle Number🔢")

    submitted=st.form_submit_button("🤖 Predict Stop Outcome & Violation")

# Function to predict violation and outcome
def predict_violation_and_outcome(df):
    if df["driver_age"] < 18:
        violation = "reckless driving"
        outcome = "citation"
    elif df["was_drug_related"]:
        violation = "drug_related offense"
        outcome = "arrest"
    else:
        violation = "speeding"
        outcome = "warning"

    return violation, outcome

if submitted:
    input_data = {
        "driver_age": driver_age,
        "was_search_conducted": search_conducted,
        "was_drug_related": drugs_related,
        "stop_time": stop_time,
        "stop_date": stop_date,
        "gender": driver_gender,
        "vehicle_number": vehicle_number,
        "stop_duration": stop_duration,
    }

    violation, outcome = predict_violation_and_outcome(input_data)

    # Display results
    st.subheader("🚔 Prediction Summary")
    st.markdown(f"- **Predicted Violation**: {violation}")
    st.markdown(f"- **Predicted Stop Outcome**: {outcome}")
    st.markdown(
        f"📄 A {driver_age}-year-old {driver_gender.lower()} driver in {country_name} was stopped at {input_data['stop_time']} on {input_data['stop_date']}. "
        f"{'A search was conducted' if search_conducted else 'No search was conducted'}, and the stop "
        f"{'was' if drugs_related else 'was not'} drug-related. "
        f"Stop duration: **{stop_duration}**. Vehicle Number: **{vehicle_number}**."
    )


#Advanced Insights Section
st.title("📊 Advanced Insights")
st.subheader("Select query to get insights")

query_mapping = {
    "1.What are the top 10 vehicle_Number involved in drug-related stops?":
    """SELECT vehicle_number, COUNT(*) AS stop_count
       FROM police_stops
       WHERE drugs_related_stop = TRUE
       GROUP BY vehicle_number
       ORDER BY stop_count DESC
       LIMIT 10;""",

    "2.Which vehicles were most frequently searched?":
    """SELECT vehicle_number, COUNT(*) AS stop_count
       FROM police_stops
       WHERE search_conducted = TRUE
       GROUP BY vehicle_number
       ORDER BY stop_count DESC
       LIMIT 10;""",

    "3.Which driver age group had the highest arrest rate?":
    """SELECT driver_age, COUNT(*) AS total_stop,
              SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests,
              ROUND(100.0 * SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END)/COUNT(*), 2) AS arrested_rate
       FROM police_stops
       WHERE driver_age IS NOT NULL
       GROUP BY driver_age
       ORDER BY arrested_rate DESC
       LIMIT 5;""",

    "4.What is the gender distribution of drivers stopped in each country?":
    """SELECT country_name, driver_gender, COUNT(*) AS total_stop
       FROM police_stops
       WHERE country_name IS NOT NULL AND driver_gender IS NOT NULL
       GROUP BY country_name, driver_gender
       ORDER BY country_name, driver_gender;""",

    "5.Which race and gender combination has the highest search rate?":
    """SELECT driver_gender, driver_race, COUNT(*) AS total_stops,
              SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS total_search_conducted,
              ROUND(100.0 * SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END)/COUNT(*), 2) AS search_conducted_rate
       FROM police_stops
       WHERE driver_gender IS NOT NULL AND driver_race IS NOT NULL
       GROUP BY driver_gender, driver_race
       ORDER BY search_conducted_rate DESC
       LIMIT 1;""",

    "6.What time of day sees the most traffic stops?":
    """SELECT EXTRACT(HOUR FROM stop_time) AS stop_hour, COUNT(*) AS total_stop
       FROM police_stops
       WHERE stop_time IS NOT NULL
       GROUP BY stop_hour
       ORDER BY total_stop DESC
       LIMIT 1;""",

    "7.What is the average stop duration for different violations?":
    """SELECT violation,
              ROUND(AVG(CASE stop_duration
                        WHEN '0-15 Min' THEN 8
                        WHEN '16-30 Min' THEN 23
                        WHEN '30-45 Min' THEN 40
                    END), 2) AS average_duration
       FROM police_stops
       WHERE violation IS NOT NULL
       GROUP BY violation
       ORDER BY average_duration DESC;""",

    "8.Are stops during the night more likely to lead to arrests?":
    """SELECT CASE WHEN EXTRACT(HOUR FROM stop_time) BETWEEN 6 AND 19 THEN 'day' ELSE 'night' END AS day_night,
              COUNT(*) AS total_stop,
              SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrested,
              ROUND(100.0 * SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END)/COUNT(*), 2) AS arrested_rate
       FROM police_stops
       WHERE stop_time IS NOT NULL
       GROUP BY day_night
       ORDER BY day_night;""",

    "9.Which violations are most associated with searches or arrests?":
    """SELECT violation,
              COUNT(*) FILTER (WHERE search_conducted = TRUE) AS total_search,
              COUNT(*) FILTER (WHERE is_arrested = TRUE) AS total_arrested
       FROM police_stops
       GROUP BY violation
       ORDER BY total_search DESC, total_arrested DESC;""",

    "10.Which violations are most common among younger drivers (<25)?":
    """SELECT violation, COUNT(*) AS total_violation_count
       FROM police_stops
       WHERE driver_age < 25
       GROUP BY violation
       ORDER BY total_violation_count DESC;""",

    "11.Is there a violation that rarely results in search or arrest?":
    """SELECT violation,
              COUNT(*) AS total_violation_count,
              SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS search,
              SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS arrest,
              ROUND(100.0 * SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END)/COUNT(*), 2) AS total_search_rate,
              ROUND(100.0 * SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END)/COUNT(*), 2) AS total_arrest_rate
       FROM police_stops
       GROUP BY violation
       ORDER BY total_search_rate ASC, total_arrest_rate ASC;""",

    "12.Which countries report the highest rate of drug-related stops?":
    """SELECT country_name,
              COUNT(*) AS total_stop,
              SUM(CASE WHEN drugs_related_stop = TRUE THEN 1 ELSE 0 END) AS total_drugs_related_stops,
              ROUND(100.0 * SUM(CASE WHEN drugs_related_stop = TRUE THEN 1 ELSE 0 END)/COUNT(*), 2) AS drugs_related_stop_rate
       FROM police_stops
       GROUP BY country_name
       ORDER BY drugs_related_stop_rate DESC;""",

    "13.What is the arrest rate by country and violation?":
    """SELECT country_name, violation,
              COUNT(*) AS total_stop,
              SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS arrest,
              ROUND(100.0 * SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END)/COUNT(*), 2) AS arrested_rate
       FROM police_stops
       GROUP BY country_name, violation
       ORDER BY arrested_rate DESC;""",

    "14.Which country has the most stops with search conducted?":
    """SELECT country_name,
              COUNT(*) AS total_search_conducted
       FROM police_stops
       WHERE search_conducted = TRUE
       GROUP BY country_name
       ORDER BY total_search_conducted DESC
       LIMIT 1;"""
}


# Dropdown options
options = list(query_mapping.keys())
selected_query = st.selectbox("🧮 Medium level query:", options)

# Run button
if st.button("Run Query🧮"):
    sql = query_mapping[selected_query]
    df = pd.read_sql_query(sql, connection)
    st.write("### Query Results:")
    st.dataframe(df)


#complex queries
st.subheader("Complex Queries 🧠")
complex_query_mapping = {
    "1.Yearly Breakdown of Stops and Arrests by Country?":
    """
    SELECT year, country_name, total_stops, total_arrests,
           ROUND(100.0 * total_arrests / total_stops, 2) AS arreste_rate,
           SUM(total_arrests) OVER (PARTITION BY country_name ORDER BY year ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_arrests
    FROM (
        SELECT EXTRACT(YEAR FROM stop_date) AS year, country_name,
               COUNT(*) AS total_stops,
               SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests
        FROM police_stops
        GROUP BY year, country_name
    ) AS yearly_data
    ORDER BY country_name, year;
    """,

    "2.Driver Violation Trends Based on Age and Race?":
    """
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
    SELECT age_group, driver_race, violation, COUNT(*) AS violation_count
    FROM age_grouped
    GROUP BY age_group, driver_race, violation
    ORDER BY age_group, driver_race, violation_count DESC;
    """,

    "3.Time Period Analysis of Stops?":
    """
    SELECT EXTRACT(YEAR FROM stop_date) AS year,
           EXTRACT(MONTH FROM stop_date) AS month,
           EXTRACT(HOUR FROM stop_time) AS hour,
           COUNT(*) AS total_stops
    FROM police_stops
    WHERE stop_date IS NOT NULL AND stop_time IS NOT NULL
    GROUP BY year, month, hour
    ORDER BY year, month, hour;
    """,

    "4.Violations with High Search and Arrest Rates?":
    """
    SELECT violation, COUNT(*) AS total_stops,
           SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) AS total_search,
           SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrested,
           ROUND(100.0 * SUM(CASE WHEN search_conducted = TRUE THEN 1 ELSE 0 END) / COUNT(*) OVER (PARTITION BY violation), 2) AS search_rate,
           ROUND(100.0 * SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) / COUNT(*) OVER (PARTITION BY violation), 2) AS arrested_rate
    FROM police_stops
    GROUP BY violation
    ORDER BY search_rate DESC, arrested_rate DESC;
    """,

    "5.Driver Demographics by Country?":
    """
    SELECT country_name, driver_age, driver_race,
           ROUND(AVG(driver_age), 1) AS avg_age,
           COUNT(*) AS total_drivers
    FROM police_stops
    WHERE country_name IS NOT NULL
      AND driver_age IS NOT NULL
      AND driver_gender IS NOT NULL
      AND driver_race IS NOT NULL
    GROUP BY country_name, driver_age, driver_race
    ORDER BY country_name, driver_age, driver_race;
    """,

    "6.Top 5 Violations with Highest Arrest Rates?":
    """
    SELECT violation, COUNT(*) AS total_stops,
           SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests,
           ROUND(100.0 * SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END)/COUNT(*), 2) AS arrest_rate
    FROM police_stops
    WHERE violation IS NOT NULL
    GROUP BY violation
    ORDER BY arrest_rate DESC
    LIMIT 5;
    """
}

# Dropdown options
options = list(complex_query_mapping.keys())
selected_query = st.selectbox("Complex level query 🧠:", options)

# Run button
if st.button("Run complex_Query 🧠"):
    sql = complex_query_mapping[selected_query]
    df = pd.read_sql_query(sql, connection)
    st.write("### Query Results:")
    st.dataframe(df)

st.subheader("📊 Logged Vehicle Stop Data")
data = pd.read_csv('D:\\MDTE21\\Police\\traffic_stops - traffic_stops_with_vehicle_number.csv')
st.dataframe(data) 
    
