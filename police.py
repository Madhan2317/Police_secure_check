import streamlit as st
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import plotly.express as px

#Dataset Path
df = pd.read_csv('D:\\MDTE21\\Police\\traffic_stops - traffic_stops_with_vehicle_number.csv')


#total number of null values in the dataset
total_null = df.isnull().sum()

#drop any Nan values
df = df.dropna()

#save the cleaned dataset
df.to_csv('traffic_stops_cleaned.csv', index=False)

# --- STREAMLIT PAGE CONFIGURATION ---
st.set_page_config(
    layout="wide"
)

# --- PAGE CONFIGURATION ---
st.markdown("""
    <style>
    .stApp {
        background-image: url("https://t3.ftcdn.net/jpg/06/49/11/00/360_F_649110054_ZnMGBRFXklYBXpRmDR2uiMWrb9okjjJI.jpg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    .main {
        background-color: reduced transparency from 0.8 to 0 
        padding: 2rem;
        border-radius: 10px;
    }
     .block-container {
        background-color: rgba(30,25,40, 0.75);
        padding: 2rem;
        border-radius: 12px;
        layout: wide;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<h1 style='text-align: center;'>🚓 Police Check Post Logging System</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size:18px;'>An interactive dashboard for monitoring and predicting outcomes of vehicle stops.</p>", unsafe_allow_html=True)

# --- DATABASE CONNECTION ---
conn = psycopg2.connect(
    host="localhost",
    database="Policestop",
    user="postgres",
    password="Madhan2317",
    port="5432"
)

# --- FORM FOR LOGGING DATA ---
with st.form("police_log_form"):
        st.markdown("#### Fill in Stop Details")
        stop_date = st.date_input("📅 Stop Date")
        stop_time = st.time_input("🕒 Stop Time")
        country_name = st.text_input("🌐 Country Name")
        driver_gender = st.selectbox("🚻 Driver Gender", ["Male 👨", "Female 👩", "Other ⚧️"])
        driver_age = st.number_input("🎂 Driver Age", min_value=16, max_value=100)
        driver_race = st.text_input("🧑🏾‍🤝‍🧑🏻 Driver Race")
        search_conducted = st.radio("🔍 Was a Search Conducted?", ["Yes", "No"])
        search_type = st.text_input("🔎 Search Type")
        drugs_related = st.radio("💊 Drug Related Stop?", ["Yes", "No"])
        stop_duration = st.selectbox("⏱ Stop Duration", ["0-15 Min", "16-30 Min", "30+ Min"])
        vehicle_number = st.text_input("🚗 Vehicle Number")

        submitted = st.form_submit_button("🚀 Predict Outcome & Log")
        if submitted:
            predicted_outcome = "Arrested" if driver_age > 20 and drugs_related == "Yes" else "Not Arrested" 
            predicted_violation = "Speeding" if search_conducted == "Yes" else "No Violation"

            st.success("🚔 Stop Logged Successfully!")
            st.info(f"🧠 Prediction: **{predicted_outcome}** for **{predicted_violation}**")

# --- PREDICTION SUMMARY ---
if submitted:
    # Display results
    st.subheader("🚔 Prediction Summary")
    st.markdown(f"- **Predicted Violation**: {predicted_violation}")
    st.markdown(f"- **Predicted Stop Outcome**: {predicted_outcome}")
    st.markdown(
        f"📄 A {driver_age}-year-old {driver_gender.lower()} driver in {country_name} was stopped at {'stop_time'} on {'stop_date'}. "
        f"{'A search was conducted' if search_conducted else 'No search was conducted'}, and the stop "
        f"{'was' if drugs_related else 'was not'} drug-related. "
        f"Stop duration: **{stop_duration}**. Vehicle Number: **{vehicle_number}**."
    )

# --- SQL QUERY MAPPINGS ---
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
# --- COMPLEX QUERIES ---
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

# data visualization

col1,col2 = st.columns(2)

col1.subheader("📊 Violation Distribution")
with col1:
    violation_counts = df['violation'].value_counts().reset_index()
    violation_counts.columns = ['Violation Category', 'Count']
    fig = px.bar(violation_counts, x='Violation Category', y='Count', title="Stop Violations Distribution")
    st.plotly_chart(fig)
    st.metric("🚦 Total Stops", int(violation_counts['Count'].sum()))

col2.subheader("Gender Distribution of Drivers")
with col2:
    gender_counts = df['driver_gender'].value_counts()
    fig = px.pie(values=gender_counts.values, names=gender_counts.index, title="Driver Gender Distribution")
    st.plotly_chart(fig)
    st.metric("🚻 Total Drivers", int(gender_counts.sum()))

col1.subheader("Top 4 countries with highest stops")
with col1:
    country_counts = df['country_name'].value_counts().head(4)
    fig = px.bar(country_counts, x=country_counts.index, y=country_counts.values, title="Top 4 Countries with Highest Stops")
    st.plotly_chart(fig)
    st.metric("🌍 Total Stops", int(country_counts.sum()))

col2.subheader("Drug-Related Arrests")
with col2:
    drug_related_counts = df['drugs_related_stop'].value_counts()
    fig = px.pie(values=drug_related_counts.values, names=drug_related_counts.index, title="Drug-Related Arrests")
    st.plotly_chart(fig)
    st.metric("🚨 Drug-Related Arrests", int(drug_related_counts.sum()))

# --- QUERY TABS ---
tab1, tab2 = st.tabs(["📊 Medium-Level Queries", "🧠 Complex-Level Queries"])

with tab1:
    selected_query = st.selectbox("Select a Medium Query", list(query_mapping.keys()))
    if st.button("Run Query 🔎"):
        sql = query_mapping[selected_query]
        df = pd.read_sql_query(sql, conn)
        st.dataframe(df)

with tab2:
    selected_complex = st.selectbox("Select a Complex Query", list(complex_query_mapping.keys()))
    if st.button("Run Complex Query 🧠"):
        sql = complex_query_mapping[selected_complex]
        df = pd.read_sql_query(sql, conn)
        st.dataframe(df)

# --- SHOW ALL DATA ---
with st.expander("📋 View Raw Stop Data"):
    st.dataframe(df)
# --- FOOTER ---
st.markdown("---")  
