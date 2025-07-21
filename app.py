import streamlit as st
import pandas as pd
import datetime
import json
import os
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from streamlit_calendar import calendar

# --- 설정 ---
st.set_page_config(page_title="📅 볼빨간사춘기 스케줄 관리", layout="wide")
SHEET_NAME = "bol4_schedule_data"
CREDENTIALS_FILE = "bol4schedule-e1056ca75cd1.json"

# --- Google Sheets 인증 ---
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)

try:
    sheet = client.open(SHEET_NAME).sheet1
except Exception as e:
    st.error(f"❌ 구글 시트 열기에 실패했습니다: {e}")
    st.stop()

# --- 데이터 불러오기 및 저장 ---
def load_schedule():
    records = sheet.get_all_records()
    return pd.DataFrame(records)

def save_schedule(df):
    sheet.clear()
    sheet.append_row(df.columns.tolist())
    for row in df.values.tolist():
        sheet.append_row(row)

# --- 마지막 수정일 표시 ---
def show_last_modified():
    try:
        cell = sheet.cell(1, 1)  # 헤더가 있으니 수정 시간은 따로 저장한 경우에만 해당
        st.markdown(f"<small>📅 마지막 수정일: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small>", unsafe_allow_html=True)
    except:
        pass

# --- Geolocation ---
geolocator = Nominatim(user_agent="calendar_app")

# --- 관리자 로그인 ---
with st.expander("🔐 관리자 로그인"):
    password = st.text_input("비밀번호", type="password")
    if "admin" not in st.session_state:
        st.session_state.admin = False
    if password == "bol4pass":
        st.session_state.admin = True
        st.success("🔓 관리자 모드 활성화됨")
    elif password != "":
        st.error("❌ 비밀번호가 틀렸습니다")

can_edit = st.session_state.get("admin", False)
edit_index = st.session_state.get("edit_index", None)

# --- 타이틀 ---
st.title("📅 볼빨간사춘기 스케줄 관리")
show_last_modified()

# --- 데이터 불러오기 ---
df = load_schedule()
df_columns = ["Date", "Time", "Title", "Memo", "Location"]
if df.empty:
    df = pd.DataFrame(columns=df_columns)

# --- 일정 추가 / 수정 폼 ---
if can_edit:
    st.subheader("✏️ 일정 추가 / 수정")

    if edit_index is not None and edit_index < len(df):
        row = df.loc[edit_index]
        default_date = pd.to_datetime(row["Date"]).date()
        default_time = datetime.time.fromisoformat(row["Time"])
        default_title = row["Title"]
        default_memo = row["Memo"]
        default_location = row["Location"]
    else:
        default_date = datetime.date.today()
        default_time = datetime.datetime.now().replace(second=0, microsecond=0).time()
        default_title = ""
        default_memo = ""
        default_location = ""

    with st.form("form_add"):
        col1, col2 = st.columns([1, 1])
        with col1:
            date = st.date_input("날짜", default_date)
        with col2:
            time = st.time_input("시간", default_time, step=datetime.timedelta(minutes=30))

        title = st.text_input("일정 제목", default_title)
        memo = st.text_area("메모", default_memo)
        location_input = st.text_input("장소 또는 주소", default_location)

        geocode_button = st.form_submit_button("주소 검색 및 저장")

        if geocode_button:
            try:
                geocoded = geolocator.geocode(location_input)
                if geocoded:
                    location = geocoded.address
                else:
                    location = location_input
            except:
                location = location_input

            new_row = pd.DataFrame([[str(date), time.strftime("%H:%M"), title, memo, location]], columns=df_columns)

            if edit_index is not None:
                df.loc[edit_index] = new_row.iloc[0]
                st.session_state.edit_index = None
                st.success("✅ 일정이 수정되었습니다.")
            else:
                df = pd.concat([df, new_row], ignore_index=True)
                st.success("✅ 일정이 추가되었습니다.")

            save_schedule(df)
            st.rerun()

# --- 일정 목록 ---
if not df.empty:
    st.subheader("📋 일정 목록")
    for i, row in df.iterrows():
        with st.container():
            st.markdown(f"**{row['Date']} {row['Time']}~ - {row['Title']}**")
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

# --- 캘린더 보기 ---
st.subheader("🗓️ 달력 보기")
if not df.empty:
    events = [{
        "title": f"{row['Time']}~ {row['Title']}",
        "start": f"{row['Date']}T{row['Time']}",
        "end": f"{row['Date']}T{row['Time']}",
        "color": "red",
    } for _, row in df.iterrows()]

    calendar(options={
        "initialView": "dayGridMonth",
        "events": events,
        "editable": False,
        "locale": "ko"
    })
else:
    st.info("캘린더에 표시할 일정이 없습니다.")

# --- 지도 보기 (항상 맨 아래에 위치) ---
st.subheader("🗺️ 지도 보기")
if not df.empty:
    m = folium.Map(location=[36.5, 127.8], zoom_start=7, max_bounds=True)
    m.fit_bounds([[33.0, 124.5], [38.7, 131.2]])
    marker_cluster = MarkerCluster().add_to(m)

    for _, row in df.iterrows():
        if row["Location"]:
            try:
                loc = geolocator.geocode(row["Location"])
                if loc:
                    folium.Marker(
                        location=[loc.latitude, loc.longitude],
                        popup=f"{row['Title']} ({row['Location']})",
                        icon=folium.Icon(color="red")
                    ).add_to(marker_cluster)
            except:
                continue

    st_folium(m, width=800, height=400)
else:
    st.info("지도에 표시할 일정이 없습니다.")
