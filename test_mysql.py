
import streamlit as st
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

try:
    cfg = st.secrets["mysql"]
    password = quote_plus(cfg["password"])

    url = (
        f"mysql+pymysql://{cfg['username']}:{password}"
        f"@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    )

    engine = create_engine(url, pool_pre_ping=True)

    with engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM sensor_data")
        ).scalar()

    print("MySQL connection successful!")
    print("Total records:", count)

except Exception as e:
    print("Connection failed:", e)
