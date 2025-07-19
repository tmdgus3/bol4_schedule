import streamlit as st
import pandas as pd
import datetime
import os
from streamlit_folium import st_folium
import folium
from geopy.geocoders import Nominatim
from streamlit_calendar import calendar

DATA_PATH = "schedule.csv"
geolocator = Nominatim(user_agent="calendar_app")

# CSV 불러오기
def load_schedule():
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
    else:
        return pd.DataFrame(columns=["Date", "Time", "Title", "Memo", "Location"])

def save_schedule(df):
    df.to_csv(DATA_PATH, index=False)

df = load_schedule()
st.set_page_config(page_title="📅 일정 캘린더", layout="wide")

st.title("📅 일정 캘린더 + 지도")

# 비밀번호 입력
password = st.sidebar.text_input("🔐 비밀번호", type="password")
can_edit = password == "bol4pass"

if can_edit:
    st.subheader("✏️ 새 일정 추가")
    with st.form("form_add"):
        date = st.date_input("날짜", datetime.date.today())
        time = st.time_input("시간", datetime.datetime.now().time(), step=datetime.timedelta(minutes=30))
        title = st.text_input("일정 제목")
        memo = st.text_area("메모")
        location = st.text_input("장소 또는 주소", "")
        submitted = st.form_submit_button("추가")

        if submitted:
            new_row = pd.DataFrame([[date, time, title, memo, location]], columns=df.columns)
            df = pd.concat([df, new_row], ignore_index=True)
            save_schedule(df)
            st.success("✅ 일정이 저장되었습니다.")
            st.experimental_rerun()

# 🗓️ 캘린더에 표시
st.subheader("📌 달력 보기")

if not df.empty:
    events = [
        {
            "title": row["Title"],
            "start": f"{row['Date']}T{row['Time']}",
            "end": f"{row['Date']}T{row['Time']}",
            "color": "red",
        }
        for _, row in df.iterrows()
    ]

    calendar_options = {
        "initialView": "dayGridMonth",
        "events": events,
        "editable": False,
        "locale": "ko",
    }

    calendar(calendar_options, height=500)

else:
    st.info("현재 등록된 일정이 없습니다.")

# 📍 지도 표시
st.subheader("🗺️ 지도 보기")

if not df.empty and "Location" in df.columns:
    m = folium.Map(location=[37.5665, 126.9780], zoom_start=5)  # 기본 서울

    for _, row in df.iterrows():
        if row["Location"]:
            try:
                location = geolocator.geocode(row["Location"])
                if location:
                    folium.Marker(
                        location=[location.latitude, location.longitude],
                        popup=row["Title"],
                        icon=folium.Icon(color="red")
                    ).add_to(m)
            except:
                continue

    st_folium(m, width=800, height=400)
else:
    st.info("표시할 위치 정보가 없습니다.")
