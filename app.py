import streamlit as st
import pandas as pd
import datetime
import os
from streamlit_folium import st_folium
import folium
from geopy.geocoders import Nominatim
from streamlit_calendar import calendar

# 설정
st.set_page_config(page_title="📅 일정 캘린더 + 지도", layout="wide")
DATA_PATH = "schedule.csv"
geolocator = Nominatim(user_agent="calendar_app")

def load_schedule():
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
    else:
        return pd.DataFrame(columns=["Date", "Time", "Title", "Memo", "Location"])

def save_schedule(df):
    df.to_csv(DATA_PATH, index=False)

df = load_schedule()

# 로그인 상태
password = st.sidebar.text_input("비밀번호 입력", type="password")
can_edit = password == "bol4pass"
edit_index = st.session_state.get("edit_index", None)

# 일정 추가/수정 폼
st.title("📅 일정 캘린더 + 지도")

if can_edit:
    st.subheader("✏️ 일정 추가 / 수정")

    if edit_index is not None:
        row = df.loc[edit_index]
        default_date = pd.to_datetime(row["Date"]).date()
        default_time = datetime.datetime.strptime(row["Time"], "%H:%M:%S").time()
        default_title = row["Title"]
        default_memo = row["Memo"]
        default_location = row["Location"]
    else:
        default_date = datetime.date.today()
        default_time = datetime.datetime.now().time()
        default_title = ""
        default_memo = ""
        default_location = ""

    with st.form("form_add"):
        date = st.date_input("날짜", default_date)
        time = st.time_input("시간", default_time, step=datetime.timedelta(minutes=30))
        title = st.text_input("일정 제목", default_title)
        memo = st.text_area("메모", default_memo)
        location = st.text_input("장소 또는 주소", default_location)
        submitted = st.form_submit_button("저장")

        if submitted:
            new_data = pd.DataFrame([[date, time, title, memo, location]], columns=df.columns)
            if edit_index is not None:
                df.loc[edit_index] = new_data.iloc[0]
                st.success("✅ 일정이 수정되었습니다.")
                st.session_state.edit_index = None
            else:
                df = pd.concat([df, new_data], ignore_index=True)
                st.success("✅ 일정이 추가되었습니다.")
            save_schedule(df)
            st.rerun()

# 📌 일정 목록 + 수정/삭제
if not df.empty:
    st.subheader("📋 일정 목록")

    for i in df.index:
        row = df.loc[i]
        with st.container():
            st.markdown(f"**{row['Date']} {row['Time']} - {row['Title']}**")
            st.caption(f"{row['Memo']}")
            st.caption(f"📍 {row['Location']}")

            if can_edit:
                col1, col2 = st.columns([1, 1])
                if col1.button("✏️ 수정", key=f"edit_{i}"):
                    st.session_state.edit_index = i
                    st.rerun()
                if col2.button("🗑️ 삭제", key=f"delete_{i}"):
                    df = df.drop(i).reset_index(drop=True)
                    save_schedule(df)
                    st.success("🗑️ 삭제 완료")
                    st.rerun()
else:
    st.info("등록된 일정이 없습니다.")

# 📅 캘린더
st.subheader("🗓️ 달력 보기")
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
    calendar(options={
        "initialView": "dayGridMonth",
        "events": events,
        "editable": False,
        "locale": "ko"
    })
else:
    st.info("캘린더에 표시할 일정이 없습니다.")

# 🗺️ 지도
st.subheader("🗺️ 지도 보기")
if not df.empty:
    m = folium.Map(location=[36.5, 127.8], zoom_start=7, max_bounds=True)
    m.fit_bounds([[33.0, 124.5], [38.7, 131.2]])
    for _, row in df.iterrows():
        if row["Location"]:
            try:
                loc = geolocator.geocode(row["Location"])
                if loc:
                    folium.Marker(
                        location=[loc.latitude, loc.longitude],
                        popup=f"{row['Title']} ({row['Location']})",
                        icon=folium.Icon(color="red", icon="map-marker")
                    ).add_to(m)
            except:
                continue
    st_folium(m, width=800, height=400)
else:
    st.info("지도에 표시할 일정이 없습니다.")
