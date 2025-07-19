import streamlit as st
import pandas as pd
import datetime
import os
from streamlit_folium import st_folium
import folium
from geopy.geocoders import Nominatim
from streamlit_calendar import calendar

# 기본 설정
st.set_page_config(page_title="📅 일정 캘린더 + 지도", layout="wide")
DATA_PATH = "schedule.csv"
geolocator = Nominatim(user_agent="calendar_app")

# 일정 불러오기
def load_schedule():
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
    else:
        return pd.DataFrame(columns=["Date", "Time", "Title", "Memo", "Location"])

# 일정 저장
def save_schedule(df):
    df.to_csv(DATA_PATH, index=False)

# 데이터 로드
df = load_schedule()

# 제목
st.title("📅 일정 캘린더 + 지도")
st.caption("🔒 수정은 비밀번호를 입력한 사람만 가능해요.")

# 비밀번호 입력
password = st.sidebar.text_input("비밀번호 입력", type="password")
can_edit = password == "bol4pass"  # 원하는 비밀번호로 바꿔도 돼요

# 일정 추가 폼
if can_edit:
    st.subheader("✏️ 새 일정 추가")
    with st.form("form_add"):
        date = st.date_input("날짜", datetime.date.today())
        time = st.time_input("시간", datetime.datetime.now().time(), step=datetime.timedelta(minutes=30))
        title = st.text_input("일정 제목")
        memo = st.text_area("메모")
        location = st.text_input("장소 또는 주소", placeholder="서울시 강남구 ...")
        submitted = st.form_submit_button("저장")

        if submitted:
            new_row = pd.DataFrame([[date, time, title, memo, location]], columns=df.columns)
            df = pd.concat([df, new_row], ignore_index=True)
            save_schedule(df)
            st.success("✅ 저장 완료!")
            st.rerun()

# 🗓️ 달력 표시
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

    value = calendar(
        events=events,
        options={
            "initialView": "dayGridMonth",
            "locale": "ko",
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek"
            }
        },
        key="calendar",
    )
else:
    st.info("등록된 일정이 없습니다.")

# 🗺️ 지도 표시
st.subheader("🗺️ 지도 보기")

if not df.empty and "Location" in df.columns:
    m = folium.Map(location=[37.5665, 126.9780], zoom_start=5)  # 서울 기본값
    for _, row in df.iterrows():
        if row["Location"]:
            try:
                loc = geolocator.geocode(row["Location"])
                if loc:
                    folium.Marker(
                        location=[loc.latitude, loc.longitude],
                        popup=row["Title"],
                        icon=folium.Icon(color="red")
                    ).add_to(m)
            except:
                continue

    st_folium(m, width=800, height=400)
else:
    st.info("표시할 위치 정보가 없습니다.")
