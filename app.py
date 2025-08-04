import streamlit as st
import pandas as pd
import datetime
import os
from streamlit_folium import st_folium
import folium
from geopy.geocoders import Nominatim
from streamlit_calendar import calendar
from datetime import time as dtime

# 설정
st.set_page_config(page_title="📅 일정 캘린더 + 지도", layout="wide")
DATA_PATH = "schedule.csv"
geolocator = Nominatim(user_agent="calendar_app", timeout=10)

# 데이터 불러오기 & 저장
def load_schedule():
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
    else:
        return pd.DataFrame(columns=["Date", "Time", "Title", "Memo", "Location"])

def save_schedule(df):
    df.to_csv(DATA_PATH, index=False)

df = load_schedule()

# --- 제목 ---
st.title("📅 일정 캘린더 + 지도")

# --- 일정 목록 ---
if not df.empty:
    st.subheader("📋 일정 목록")

    for i in df.index:
        row = df.loc[i]
        with st.container():
            time_str = str(row["Time"])[:5] + "~"
            st.markdown(f"**{row['Date']} {time_str} {row['Title']}**")
            st.caption(f"{row['Memo']}")
            st.caption(f"📍 {row['Location']}")

            if st.session_state.get("admin", False):
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

# --- 캘린더 ---
st.subheader("🗓️ 달력 보기")

if not df.empty:
    events = [
        {
            "title": f"{str(row['Time'])[:5]}~ {row['Title']}",
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

# --- 지도 ---
st.subheader("🗺️ 지도 보기")

if not df.empty:
    m = folium.Map(location=[36.5, 127.8], zoom_start=7, max_bounds=True)
    # 대한민국 영역 제한
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

# --- 일정 추가/수정 폼 ---
if "admin" not in st.session_state:
    st.session_state.admin = False
can_edit = st.session_state.get("admin", False)
edit_index = st.session_state.get("edit_index", None)

if can_edit:
    st.subheader("✏️ 일정 추가 / 수정")

    if edit_index is not None and edit_index in df.index:
        row = df.loc[edit_index]
        default_date = pd.to_datetime(row["Date"]).date()
        time_str = row["Time"]
        try:
            default_time = dtime.fromisoformat(time_str)
        except:
            default_time = datetime.datetime.now().time()
        default_title = row["Title"]
        default_memo = row["Memo"]
        default_location = row["Location"]
    else:
        edit_index = None
        st.session_state.edit_index = None
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
        address_input = st.text_input("장소 또는 주소", default_location)

        # 주소 검색 버튼
        if st.form_submit_button("주소 검색 🔍"):
            if address_input:
                try:
                    loc = geolocator.geocode(address_input)
                    if loc:
                        st.success(f"✅ 위치 찾음: {loc.address}")
                        folium_static_map = folium.Map(location=[loc.latitude, loc.longitude], zoom_start=16)
                        folium.Marker(location=[loc.latitude, loc.longitude], popup=address_input).add_to(folium_static_map)
                        st_folium(folium_static_map, width=700, height=300)
                except Exception as e:
                    st.error("❌ 주소 검색 실패")

        submitted = st.form_submit_button("저장")
        if submitted:
            new_data = pd.DataFrame([[date, time, title, memo, address_input]], columns=df.columns)
            if edit_index is not None:
                df.loc[edit_index] = new_data.iloc[0]
                st.success("✅ 일정이 수정되었습니다.")
                st.session_state.edit_index = None
            else:
                df = pd.concat([df, new_data], ignore_index=True)
                st.success("✅ 일정이 추가되었습니다.")
            save_schedule(df)
            st.rerun()

# --- 관리자 로그인 (맨 아래로 이동) ---
with st.expander("🔐 관리자 로그인"):
    password = st.text_input("비밀번호", type="password")
    if password == "bol4pass":
        st.session_state.admin = True
        st.success("🔓 관리자 모드 활성화됨")
    elif password != "":
        st.error("❌ 비밀번호가 틀렸습니다")
