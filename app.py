
import os
import re
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import SQLAlchemyError


# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="IoT Cloud Analytics",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# DARK NAVY UI
# ============================================================
st.markdown(
    """
    <style>
    :root {
        --navy: #0b1120;
        --panel: #111c31;
        --panel2: #16243b;
        --border: #263650;
        --text: #e5edf9;
        --muted: #91a4bf;
        --blue: #60a5fa;
        --cyan: #22d3ee;
        --green: #34d399;
    }

    .stApp {
        background:
            radial-gradient(ellipse at 10% 0%, #142543 0%, transparent 38%),
            #0b1120;
        color: var(--text);
    }

    [data-testid="stHeader"] {
        background: rgba(11, 17, 32, 0.88);
    }

    [data-testid="stSidebar"] {
        background: #0e182a;
        border-right: 1px solid #263650;
    }

    [data-testid="stSidebar"] * {
        color: #dbeafe;
    }

    .block-container {
        max-width: 1600px;
        padding-top: 1.7rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #edf5ff !important;
        letter-spacing: -0.4px;
    }

    h1 {
        font-size: 2.25rem !important;
        font-weight: 800 !important;
    }

    h2 {
        font-size: 1.45rem !important;
    }

    p, label, .stMarkdown {
        color: #d3deef;
    }

    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #16243b, #101a2c);
        border: 1px solid #2b3c58;
        border-radius: 16px;
        padding: 19px 20px;
        min-height: 128px;
        box-shadow: 0 8px 24px rgba(0,0,0,.12);
    }

    [data-testid="stMetricLabel"] {
        color: #9fb2cc !important;
        font-size: .92rem !important;
    }

    [data-testid="stMetricValue"] {
        color: #f3f8ff !important;
        font-size: 1.85rem !important;
        font-weight: 750 !important;
    }

    [data-testid="stMetricDelta"] {
        font-size: .82rem !important;
    }

    div[data-testid="stPlotlyChart"],
    div[data-testid="stDataFrame"] {
        background: #111c31;
        border: 1px solid #263650;
        border-radius: 14px;
        padding: 8px;
    }

    .hero {
        background: linear-gradient(115deg, #162a49, #101a2c 75%);
        border: 1px solid #2d4264;
        border-radius: 20px;
        padding: 25px 28px;
        margin-bottom: 22px;
    }

    .hero-label {
        color: #60a5fa;
        font-size: .78rem;
        font-weight: 800;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    .hero-subtitle {
        color: #a9bbd4;
        font-size: 1rem;
        margin-top: 5px;
    }

    .section-label {
        color: #60a5fa;
        font-size: .77rem;
        font-weight: 800;
        letter-spacing: 1.7px;
        text-transform: uppercase;
        margin-top: 10px;
        margin-bottom: 5px;
    }

    .status-pill {
        display: inline-block;
        background: #12382f;
        color: #6ee7b7;
        padding: 6px 11px;
        border: 1px solid #20644e;
        border-radius: 30px;
        font-size: .78rem;
        font-weight: 700;
    }

    .chat-user {
        background: #19345a;
        border: 1px solid #315782;
        border-radius: 15px 15px 3px 15px;
        padding: 13px 16px;
        margin: 10px 0 8px 15%;
        color: #f0f7ff;
    }

    .chat-assistant {
        background: #142238;
        border: 1px solid #2a405e;
        border-radius: 15px 15px 15px 3px;
        padding: 15px 17px;
        margin: 8px 10% 14px 0;
        color: #dce8f8;
        line-height: 1.65;
    }

    .chat-name {
        font-size: .76rem;
        font-weight: 800;
        color: #60a5fa;
        margin-bottom: 5px;
    }

    .small-muted {
        color: #8da2bd;
        font-size: .83rem;
    }

    div.stButton > button {
        border-radius: 10px;
        border: 1px solid #314865;
        background: #172943;
        color: #eaf3ff;
        font-weight: 600;
        min-height: 42px;
    }

    div.stButton > button:hover {
        border-color: #60a5fa;
        color: #ffffff;
        background: #203a5c;
    }

    div[data-testid="stForm"] {
        background: #111c31;
        border: 1px solid #2b3c58;
        border-radius: 14px;
        padding: 15px;
    }

    input, textarea {
        color: #eef5ff !important;
    }

    [data-baseweb="select"] > div {
        background-color: #16243b;
        border-color: #334766;
    }

    hr {
        border-color: #263650;
    }

    #MainMenu, footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CONSTANTS AND SESSION STATE
# ============================================================
COLORS = [
    "#60a5fa",
    "#34d399",
    "#fbbf24",
    "#c084fc",
    "#22d3ee",
    "#fb7185",
    "#a3e635",
    "#f97316",
]

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "chat_input_value" not in st.session_state:
    st.session_state.chat_input_value = ""


# ============================================================
# DEMO DATA
# ============================================================
def create_sample_data():
    import numpy as np

    rng = np.random.default_rng(42)
    times = pd.date_range(
        end=pd.Timestamp.now().floor("h"),
        periods=240,
        freq="h",
    )

    records = []

    for number in range(1, 5):
        for timestamp in times:
            temperature = (
                25
                + number * 0.8
                + 3 * np.sin(timestamp.hour * 2 * np.pi / 24)
                + rng.normal(0, 1.2)
            )

            humidity = (
                65
                - number * 2
                - (temperature - 25) * 0.8
                + rng.normal(0, 4)
            )

            records.append({
                "sensor_id": f"SENSOR_{number:02d}",
                "timestamp": timestamp,
                "temperature": round(float(temperature), 2),
                "humidity": round(
                    float(max(20, min(95, humidity))), 2
                ),
            })

    return pd.DataFrame(records)


# ============================================================
# DATA CLEANING
# ============================================================
def clean_data(data):
    data = data.copy()

    data.columns = (
        data.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[\s\-]+", "_", regex=True)
    )

    aliases = {
        "sensorid": "sensor_id",
        "device_id": "sensor_id",
        "deviceid": "sensor_id",
        "time": "timestamp",
        "datetime": "timestamp",
        "date_time": "timestamp",
        "temp": "temperature",
        "temp_c": "temperature",
        "humidity_percent": "humidity",
        "relative_humidity": "humidity",
    }

    data = data.rename(columns=aliases)

    required = [
        "sensor_id",
        "timestamp",
        "temperature",
        "humidity",
    ]

    missing = [column for column in required if column not in data]

    if missing:
        raise ValueError(
            f"Missing columns: {', '.join(missing)}. "
            "Required columns: sensor_id, timestamp, "
            "temperature, humidity."
        )

    initial_count = len(data)

    data["sensor_id"] = (
        data["sensor_id"].astype("string").str.strip()
    )

    data["timestamp"] = pd.to_datetime(
        data["timestamp"], errors="coerce", utc=True
    ).dt.tz_convert(None)

    for column in ["temperature", "humidity"]:
        data[column] = pd.to_numeric(
            data[column], errors="coerce"
        )

    data = data.dropna(subset=required)
    data = data[data["sensor_id"] != ""]
    data = data[data["humidity"].between(0, 100)]

    # Keep the latest occurrence of each sensor/timestamp pair.
    data = data.drop_duplicates(
        subset=["sensor_id", "timestamp"],
        keep="last",
    )

    data = data.sort_values("timestamp").reset_index(drop=True)

    return data, initial_count - len(data)


# ============================================================
# MYSQL / AMAZON RDS
# ============================================================
def get_mysql_config():
    try:
        config = st.secrets["mysql"]
        return {
            "host": config["host"],
            "port": int(config.get("port", 3306)),
            "database": config["database"],
            "username": config["username"],
            "password": config["password"],
            "table": config.get("table", "sensor_data"),
        }
    except (KeyError, FileNotFoundError):
        pass

    return {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "database": os.getenv("DB_NAME"),
        "username": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "table": os.getenv("DB_TABLE", "sensor_data"),
    }


def load_from_mysql():
    config = get_mysql_config()

    required = [
        config["host"],
        config["database"],
        config["username"],
        config["password"],
    ]

    if not all(required):
        raise ValueError(
            "Database settings are missing. Configure "
            ".streamlit/secrets.toml or the DB_HOST, DB_NAME, "
            "DB_USER and DB_PASSWORD environment variables."
        )

    table = config["table"]

    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table):
        raise ValueError("Invalid table name in database settings.")

    db_url = URL.create(
        "mysql+pymysql",
        username=config["username"],
        password=config["password"],
        host=config["host"],
        port=config["port"],
        database=config["database"],
    )

    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 8},
    )

    try:
        query = text(
            f"""
            SELECT sensor_id, timestamp, temperature, humidity
            FROM `{table}`
            ORDER BY timestamp
            """
        )

        with engine.connect() as connection:
            result = pd.read_sql(query, connection)
    finally:
        engine.dispose()

    if result.empty:
        raise ValueError("The selected MySQL table has no records.")

    return result


# ============================================================
# CHART THEME
# ============================================================
def style_chart(fig, height=350):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Arial, sans-serif",
            color="#cbd5e1",
            size=12,
        ),
        title=dict(
            font=dict(size=16, color="#e5edf9"),
            x=0.02,
        ),
        height=height,
        margin=dict(l=15, r=15, t=60, b=20),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
        hoverlabel=dict(
            bgcolor="#16243b",
            font_color="#f1f5f9",
        ),
    )

    fig.update_xaxes(
        gridcolor="#24334a",
        zerolinecolor="#24334a",
    )

    fig.update_yaxes(
        gridcolor="#24334a",
        zerolinecolor="#24334a",
    )

    return fig


# ============================================================
# DATA-DRIVEN CHAT INSIGHTS
# No external AI API key required.
# ============================================================
def answer_question(question, data):
    q = question.lower().strip()

    if data.empty:
        return "There are no records in the current filter to analyze."

    count = len(data)
    sensor_count = data["sensor_id"].nunique()

    avg_temp = data["temperature"].mean()
    avg_humidity = data["humidity"].mean()

    hottest = data.loc[data["temperature"].idxmax()]
    coldest = data.loc[data["temperature"].idxmin()]
    most_humid = data.loc[data["humidity"].idxmax()]

    sensor_stats = (
        data.groupby("sensor_id")
        .agg(
            avg_temp=("temperature", "mean"),
            avg_humidity=("humidity", "mean"),
            readings=("temperature", "size"),
        )
        .round(2)
    )

    if any(word in q for word in [
        "hello", "hi", "hey", "help"
    ]):
        return (
            f"Hello! I'm your IoT Data Assistant. I can analyze "
            f"{count:,} readings from {sensor_count} sensors. "
            "Ask me about temperature, humidity, maximum or "
            "minimum readings, sensor comparisons, or trends."
        )

    if "hottest sensor" in q or "highest temperature sensor" in q:
        sensor = sensor_stats["avg_temp"].idxmax()
        value = sensor_stats.loc[sensor, "avg_temp"]
        return (
            f"**{sensor}** has the highest average temperature "
            f"at **{value:.2f} °C** in the current selection."
        )

    if "coolest sensor" in q or "lowest temperature sensor" in q:
        sensor = sensor_stats["avg_temp"].idxmin()
        value = sensor_stats.loc[sensor, "avg_temp"]
        return (
            f"**{sensor}** has the lowest average temperature "
            f"at **{value:.2f} °C** in the current selection."
        )

    if "most humid sensor" in q or "highest humidity sensor" in q:
        sensor = sensor_stats["avg_humidity"].idxmax()
        value = sensor_stats.loc[sensor, "avg_humidity"]
        return (
            f"**{sensor}** has the highest average humidity "
            f"at **{value:.2f}%** in the current selection."
        )

    if "least humid sensor" in q or "lowest humidity sensor" in q:
        sensor = sensor_stats["avg_humidity"].idxmin()
        value = sensor_stats.loc[sensor, "avg_humidity"]
        return (
            f"**{sensor}** has the lowest average humidity "
            f"at **{value:.2f}%** in the current selection."
        )

    if "maximum temperature" in q or "highest temperature" in q:
        return (
            f"The maximum recorded temperature is "
            f"**{hottest['temperature']:.2f} °C**, from "
            f"**{hottest['sensor_id']}** at "
            f"{hottest['timestamp']} UTC."
        )

    if "minimum temperature" in q or "lowest temperature" in q:
        return (
            f"The minimum recorded temperature is "
            f"**{coldest['temperature']:.2f} °C**, from "
            f"**{coldest['sensor_id']}** at "
            f"{coldest['timestamp']} UTC."
        )

    if "maximum humidity" in q or "highest humidity" in q:
        return (
            f"The maximum recorded humidity is "
            f"**{most_humid['humidity']:.2f}%**, from "
            f"**{most_humid['sensor_id']}** at "
            f"{most_humid['timestamp']} UTC."
        )

    if "average" in q or "mean" in q or "overall" in q:
        if "humidity" in q:
            return f"The average humidity is **{avg_humidity:.2f}%**."
        if "temperature" in q or "temp" in q:
            return f"The average temperature is **{avg_temp:.2f} °C**."
        return (
            f"For the current selection, average temperature is "
            f"**{avg_temp:.2f} °C** and average humidity is "
            f"**{avg_humidity:.2f}%**."
        )

    if "compare" in q or "sensor-wise" in q or "sensor wise" in q:
        lines = [
            f"- **{sensor}**: average temperature "
            f"{row['avg_temp']:.2f} °C; average humidity "
            f"{row['avg_humidity']:.2f}% "
            f"({int(row['readings'])} readings)"
            for sensor, row in sensor_stats.iterrows()
        ]
        return "Here is the sensor comparison:\n\n" + "\n".join(lines)

    if "trend" in q or "over time" in q or "increasing" in q:
        ordered = data.sort_values("timestamp")
        midpoint = max(1, len(ordered) // 2)
        first_half = ordered.iloc[:midpoint]
        second_half = ordered.iloc[midpoint:]

        if second_half.empty:
            return "There are not enough records to compare trends."

        change = (
            second_half["temperature"].mean()
            - first_half["temperature"].mean()
        )

        direction = (
            "increased" if change > 0.1
            else "decreased" if change < -0.1
            else "remained broadly stable"
        )

        return (
            f"Comparing the first and second halves of the selected "
            f"records, average temperature **{direction}**. "
            f"The difference is **{abs(change):.2f} °C**. "
            "This is a simple comparison, not a statistical forecast."
        )

    if "how many" in q or "number of readings" in q or "count" in q:
        return (
            f"The current selection contains **{count:,} readings** "
            f"across **{sensor_count} sensors**."
        )

    if "min" in q and "humidity" in q:
        row = data.loc[data["humidity"].idxmin()]
        return (
            f"Minimum humidity is **{row['humidity']:.2f}%**, "
            f"recorded by {row['sensor_id']} at "
            f"{row['timestamp']} UTC."
        )

    return (
        "I can answer questions about the data currently loaded in "
        "your dashboard. Try asking:\n\n"
        "- What is the average temperature?\n"
        "- Which sensor has the highest average temperature?\n"
        "- What is the maximum humidity?\n"
        "- Compare the sensors.\n"
        "- Describe the temperature trend.\n"
        "- How many readings are available?\n\n"
        "This assistant uses built-in analytical rules, not a "
        "connected generative AI model."
    )


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("## 🌐 IoT Analytics")
    st.caption("CLOUD INTELLIGENCE PLATFORM")
    st.markdown("---")

    st.markdown("### Data source")

    source = st.radio(
        "Choose data source",
        [
            "Demo Dataset",
            "Upload CSV",
            "MySQL / Amazon RDS",
        ],
        label_visibility="collapsed",
    )

    uploaded_file = None

    if source == "Upload CSV":
        uploaded_file = st.file_uploader(
            "Upload sensor CSV",
            type=["csv"],
        )
        st.caption(
            "Required: sensor_id, timestamp, temperature, humidity"
        )

    st.markdown("---")
    st.markdown("### Sensor filters")

    st.caption(
        "Choose the data source first. Filters appear once data loads."
    )

    st.markdown("---")
    st.markdown("### About")
    st.caption(
        "Cloud-based IoT analytics with Python, Streamlit, "
        "Plotly, and optional MySQL/RDS connectivity."
    )


# ============================================================
# HEADER AND DATA LOADING
# ============================================================
st.markdown(
    """
    <div class="hero">
        <div class="hero-label">Cloud Monitoring / Analytics</div>
        <h1 style="margin: 7px 0 0 0;">
            IoT Data Command Center
        </h1>
        <div class="hero-subtitle">
            Real-time style monitoring, sensor intelligence,
            and descriptive analytics in one workspace.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    if source == "Demo Dataset":
        raw_df = create_sample_data()
        source_name = "Demo data"

    elif source == "Upload CSV":
        if uploaded_file is None:
            st.info(
                "Upload your sensor CSV from the sidebar, "
                "or choose Demo Dataset to explore the interface."
            )
            st.stop()

        raw_df = pd.read_csv(uploaded_file)
        source_name = uploaded_file.name

    else:
        with st.spinner("Connecting to MySQL / Amazon RDS..."):
            raw_df = load_from_mysql()
        source_name = "MySQL / Amazon RDS"

    df, removed_count = clean_data(raw_df)

except (ValueError, SQLAlchemyError, KeyError) as error:
    st.error(f"Data loading failed: {error}")
    st.stop()

except Exception as error:
    st.error(f"Unable to load the selected source: {error}")
    st.stop()

if df.empty:
    st.warning("No valid sensor records remain after cleaning.")
    st.stop()

st.markdown(
    f'<span class="status-pill">● DATA LOADED</span> '
    f'<span class="small-muted">'
    f'&nbsp;Source: {source_name} &nbsp;|&nbsp; '
    f'{len(df):,} valid records &nbsp;|&nbsp; '
    f'{removed_count:,} removed during cleaning'
    f'</span>',
    unsafe_allow_html=True,
)

# ============================================================
# FILTERS
# ============================================================
with st.sidebar:
    st.markdown("### Select sensors")

    available_sensors = sorted(df["sensor_id"].unique().tolist())

    selected_sensors = st.multiselect(
        "Sensors",
        options=available_sensors,
        default=available_sensors,
        label_visibility="collapsed",
    )

    min_date = df["timestamp"].min().date()
    max_date = df["timestamp"].max().date()

    st.markdown("### Date range")

    selected_dates = st.date_input(
        "Select dates",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if st.button("Reset conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

if isinstance(selected_dates, (tuple, list)):
    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
    elif len(selected_dates) == 1:
        start_date = end_date = selected_dates[0]
    else:
        start_date, end_date = min_date, max_date
else:
    start_date = end_date = selected_dates

filtered_df = df[
    df["sensor_id"].isin(selected_sensors)
    & (df["timestamp"] >= pd.Timestamp(start_date))
    & (
        df["timestamp"]
        < pd.Timestamp(end_date) + pd.Timedelta(days=1)
    )
].copy()

if filtered_df.empty:
    st.warning(
        "No records match your filters. Select another sensor "
        "or date range in the sidebar."
    )
    st.stop()

# ============================================================
# KPI CARDS
# ============================================================
st.markdown('<div class="section-label">Overview</div>', unsafe_allow_html=True)
st.subheader("Performance at a glance")

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Total readings",
    f"{len(filtered_df):,}",
    help="Number of valid records in the current selection.",
)

k2.metric(
    "Active sensors",
    f"{filtered_df['sensor_id'].nunique():,}",
    help="Distinct sensors represented in the current selection.",
)

k3.metric(
    "Average temperature",
    f"{filtered_df['temperature'].mean():.2f} °C",
)

k4.metric(
    "Average humidity",
    f"{filtered_df['humidity'].mean():.2f}%",
)

st.markdown("---")

# ============================================================
# INTERACTIVE TRENDS
# ============================================================
st.markdown('<div class="section-label">Time series</div>', unsafe_allow_html=True)
st.subheader("Environmental trends")

left, right = st.columns(2)

with left:
    fig = px.line(
        filtered_df,
        x="timestamp",
        y="temperature",
        color="sensor_id",
        color_discrete_sequence=COLORS,
        markers=False,
        title="Temperature over time",
        labels={
            "timestamp": "Timestamp (UTC)",
            "temperature": "Temperature (°C)",
            "sensor_id": "Sensor",
        },
        hover_data={
            "temperature": ":.2f",
            "timestamp": True,
        },
    )
    fig.update_traces(line=dict(width=2.5))
    style_chart(fig)
    st.plotly_chart(fig, use_container_width=True)

with right:
    fig = px.line(
        filtered_df,
        x="timestamp",
        y="humidity",
        color="sensor_id",
        color_discrete_sequence=COLORS,
        title="Humidity over time",
        labels={
            "timestamp": "Timestamp (UTC)",
            "humidity": "Humidity (%)",
            "sensor_id": "Sensor",
        },
    )
    fig.update_traces(line=dict(width=2.5))
    style_chart(fig)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# SENSOR COMPARISON
# ============================================================
st.markdown('<div class="section-label">Sensor intelligence</div>', unsafe_allow_html=True)
st.subheader("Compare sensor performance")

summary = (
    filtered_df.groupby("sensor_id")
    .agg(
        readings=("temperature", "size"),
        avg_temperature=("temperature", "mean"),
        min_temperature=("temperature", "min"),
        max_temperature=("temperature", "max"),
        avg_humidity=("humidity", "mean"),
        min_humidity=("humidity", "min"),
        max_humidity=("humidity", "max"),
    )
    .round(2)
    .reset_index()
)

left, right = st.columns(2)

with left:
    fig = px.bar(
        summary,
        x="sensor_id",
        y="avg_temperature",
        color="sensor_id",
        color_discrete_sequence=COLORS,
        title="Average temperature by sensor",
        labels={
            "sensor_id": "Sensor",
            "avg_temperature": "Temperature (°C)",
        },
        text_auto=".2f",
    )
    fig.update_layout(showlegend=False)
    style_chart(fig)
    st.plotly_chart(fig, use_container_width=True)

with right:
    fig = px.bar(
        summary,
        x="sensor_id",
        y="avg_humidity",
        color="sensor_id",
        color_discrete_sequence=COLORS,
        title="Average humidity by sensor",
        labels={
            "sensor_id": "Sensor",
            "avg_humidity": "Humidity (%)",
        },
        text_auto=".2f",
    )
    fig.update_layout(showlegend=False)
    style_chart(fig)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# CORRELATION / DISTRIBUTION
# ============================================================
st.markdown('<div class="section-label">Deeper analysis</div>', unsafe_allow_html=True)
st.subheader("Reading patterns")

left, right = st.columns(2)

with left:
    fig = px.scatter(
        filtered_df,
        x="temperature",
        y="humidity",
        color="sensor_id",
        color_discrete_sequence=COLORS,
        hover_data=["timestamp"],
        title="Temperature vs. humidity",
        labels={
            "temperature": "Temperature (°C)",
            "humidity": "Humidity (%)",
            "sensor_id": "Sensor",
        },
    )
    style_chart(fig)
    st.plotly_chart(fig, use_container_width=True)

with right:
    fig = px.histogram(
        filtered_df,
        x="temperature",
        color="sensor_id",
        color_discrete_sequence=COLORS,
        barmode="overlay",
        opacity=0.75,
        nbins=25,
        title="Temperature distribution",
        labels={"temperature": "Temperature (°C)"},
    )
    style_chart(fig)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# DESCRIPTIVE STATISTICS
# ============================================================
st.markdown('<div class="section-label">Statistical summary</div>', unsafe_allow_html=True)
st.subheader("Descriptive analytics")

stats = (
    filtered_df[["temperature", "humidity"]]
    .describe()
    .round(2)
    .rename(
        index={
            "count": "Count",
            "mean": "Average",
            "std": "Standard deviation",
            "min": "Minimum",
            "25%": "25th percentile",
            "50%": "Median",
            "75%": "75th percentile",
            "max": "Maximum",
        }
    )
)

with st.expander("View descriptive statistics", expanded=True):
    st.dataframe(stats, use_container_width=True)

with st.expander("View sensor summary table"):
    st.dataframe(summary, use_container_width=True, hide_index=True)

with st.expander("View cleaned records"):
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
    )

# ============================================================
# CHAT-STYLE DATA ASSISTANT
# ============================================================
st.markdown("---")
st.markdown('<div class="section-label">Interactive assistant</div>', unsafe_allow_html=True)
st.subheader("💬 Ask your IoT Data Assistant")

st.caption(
    "Ask questions about the selected data. Answers are computed "
    "from the currently filtered records; no AI API key is needed."
)

suggestions = [
    "What is the average temperature?",
    "Which sensor has the highest average temperature?",
    "What is the maximum humidity?",
    "Compare the sensors.",
    "Describe the temperature trend.",
]

suggestion_cols = st.columns(len(suggestions))

for index, suggestion in enumerate(suggestions):
    with suggestion_cols[index]:
        if st.button(
            suggestion,
            key=f"suggestion_{index}",
            use_container_width=True,
        ):
            response = answer_question(suggestion, filtered_df)
            st.session_state.chat_history.append({
                "role": "user",
                "content": suggestion,
            })
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response,
            })

# Display conversation history
chat_container = st.container()

with chat_container:
    if not st.session_state.chat_history:
        st.markdown(
            """
            <div class="chat-assistant">
                <div class="chat-name">IoT DATA ASSISTANT</div>
                Hello! I can help you explore your sensor readings.
                Ask about averages, extreme values, sensor comparisons,
                or simple trends. Try one of the suggested questions.
            </div>
            """,
            unsafe_allow_html=True,
        )

    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(
                f"""
                <div class="chat-user">
                    <b>You</b><br/>
                    {message["content"]}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            # Render assistant content using Streamlit Markdown.
            with st.container():
                st.markdown(
                    '<div class="chat-assistant">'
                    '<div class="chat-name">IOT DATA ASSISTANT</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(message["content"])
                st.markdown("</div>", unsafe_allow_html=True)

with st.form("chat_form", clear_on_submit=True):
    question = st.text_input(
        "Ask a question",
        placeholder="e.g. Which sensor is hottest?",
    )
    submitted = st.form_submit_button(
        "Send message ➤",
        use_container_width=True,
    )

    if submitted and question.strip():
        st.session_state.chat_history.append({
            "role": "user",
            "content": question.strip(),
        })

        response = answer_question(question, filtered_df)

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response,
        })

        st.rerun()

# ============================================================
# DOWNLOADS
# ============================================================
st.markdown("---")
st.markdown('<div class="section-label">Export center</div>', unsafe_allow_html=True)
st.subheader("Download your analysis")

download_left, download_right = st.columns(2)

with download_left:
    st.download_button(
        "⬇ Download filtered readings",
        data=filtered_df.to_csv(index=False).encode("utf-8"),
        file_name="iot_filtered_readings.csv",
        mime="text/csv",
        use_container_width=True,
    )

with download_right:
    st.download_button(
        "⬇ Download sensor summary",
        data=summary.to_csv(index=False).encode("utf-8"),
        file_name="iot_sensor_summary.csv",
        mime="text/csv",
        use_container_width=True,
    )

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown(
    f"""
    <div style="text-align:center; color:#7185a2; padding:10px;">
        IoT Cloud Analytics &nbsp;·&nbsp;
        Python &nbsp;·&nbsp; Streamlit &nbsp;·&nbsp; Plotly &nbsp;·&nbsp; MySQL
        <br/><br/>
        Dashboard rendered {datetime.now().strftime("%d %b %Y, %H:%M:%S")}
    </div>
    """,
    unsafe_allow_html=True,
)
